import pytest
import paramiko
import subprocess
import time

server_ip = "192.168.1.115"
username = "postgres"
password = "sa"

@pytest.fixture(scope="function")
def server():
    """
    Фікстура:
      1) Підключається по SSH
      2) Убиває всі старі процеси iperf3 (якщо є)
      3) Запускає iperf3 -s у фоні (через nohup)
      4) Закриває канали stdout/stderr, щоби не блокуватися
      5) Повертає error_msg (якщо виникли якісь помилки)
      6) Нарешті, у блоці finally, зупиняє iperf і закриває SSH.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Підключаємось по SSH
        ssh_client.connect(hostname=server_ip, username=username, password=password)
        print("[Server fixture] SSH connected to:", server_ip)

        # 1) Прибираємо старі процеси iperf3, якщо вони зависли
        ssh_client.exec_command("pkill iperf3 || true")
        time.sleep(1)

        # 2) Запуск через nohup, щоб не блокуватися
        command = "nohup iperf3 -s > /dev/null 2>&1 &"
        stdin, stdout, stderr = ssh_client.exec_command(command)

        time.sleep(1)  # Дати час iPerf піднятися

        # 3) Зчитати і зафіксувати помилки запуску
        #    Зверніть увагу, що часто ці потоки будуть порожні, адже nohup відрізає вивід
        error_msg = stderr.read().decode().strip()
        if error_msg:
            print("[Server fixture] iPerf server startup error:", error_msg)

        # 4) Обов'язково закрити канали, щоб не чекати "вічно"
        stdout.channel.close()
        stderr.channel.close()

        # Передаємо керування тесту
        yield error_msg

    finally:
        # 5) Після тестів убиваємо iperf3 і закриваємо SSH
        ssh_client.exec_command("pkill iperf3 || true")
        print("[Server fixture] iperf server stopped.")
        ssh_client.close()
        print("[Server fixture] SSH connection closed.")


@pytest.fixture(scope="function")
def client(server):
    """
    Фікстура для запуску iperf-клієнта (локально) за допомогою subprocess.
    Повертає (stdout, stderr, error_msg_from_server).
    """
    error_serv = server  # Тут — рядок з фікстури server(), якщо там було щось у stderr

    cmd = [
        "iperf3", 
        "-c", server_ip, 
        "-p", "5201", 
        "-t", "2",   
        "-i", "1"
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = proc.stdout
    stderr = proc.stderr

    return stdout, stderr, error_serv
