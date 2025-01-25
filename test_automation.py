import subprocess
import re

SERVER_IP = "192.168.1.115"
PORT = 5201

########################################################################
# 1. Ping Test
########################################################################

def ping_server(server_ip):
    """
    Перевіряє, чи сервер доступний через ping.
    Повертає (True, <output>) або (False, <output>) залежно від результату.
    """
    print("=== Ping Test ===")
    try:
        # -c 4 означає 4 пакети, -W 2 означає timeout 2 секунди
        command = ["ping", "-c", "4", "-W", "2", server_ip]
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Ping Test: PASSED\n", result.stdout)
            return True, result.stdout
        else:
            print("Ping Test: FAILED\n", result.stderr)
            return False, result.stderr
    except Exception as e:
        print(f"Ping Test: ERROR {str(e)}")
        return False, str(e)


########################################################################
# 2. iPerf3 TCP Test
########################################################################

def run_iperf_client(server_ip, udp=False):
    """
    Запускає iperf3 в TCP або UDP режимі та повертає (stdout, stderr).
    Якщо трапляється виключення, повертає (None, <exception>).
    """
    try:
        command = ["iperf3", "-c", server_ip, "-p", str(PORT), "-i", "1"]
        if udp:
            command.append("-u")

        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, text=True, capture_output=True)
        return result.stdout, result.stderr

    except Exception as e:
        return None, str(e)


def parse_iperf_output(output):
    """
    Парсить стандартний вивід iperf3 та дістає потрібні інтервали.
    Повертає список словників:
    [
       {
         "Interval": "0.00-1.00",
         "Transfer": "12.34 MBytes",
         "Bitrate": "100.23 Mbits/sec"
       },
       ...
    ]
    """
    # Приклад пошуку:
    # 0.00-1.00 sec 12.34 MBytes  100.23 Mbits/sec
    pattern = r"(\d+\.\d+-\d+\.\d+)\s+sec\s+(\d+\.\d+)\s(\w+Bytes)\s+(\d+\.\d+)\s(\w+bits/sec)"
    matches = re.findall(pattern, output)

    results = []
    for match in matches:
        interval, transfer_value, transfer_unit, bitrate_value, bitrate_unit = match

        results.append({
            "Interval": interval,
            "Transfer": f"{transfer_value} {transfer_unit}",
            "Bitrate": f"{bitrate_value} {bitrate_unit}"
        })
    return results


def filter_results(parsed_results, min_transfer=2.0, min_bitrate=20.0):
    """
    Фільтрує результати за замовчуванням за умов:
    Transfer > 2 MB і Bitrate > 20 Mbits/sec.
    Повертає відфільтрований список.
    """
    filtered = []
    for entry in parsed_results:
        try:
            transfer_val_str, transfer_unit_str = entry["Transfer"].split()
            bitrate_val_str, bitrate_unit_str = entry["Bitrate"].split()

            transfer_val = float(transfer_val_str)
            bitrate_val = float(bitrate_val_str)

            # Для спрощення передбачимо, що Transfer завжди в MBytes, Bitrate у Mbits/sec
            if transfer_val > min_transfer and bitrate_val > min_bitrate:
                filtered.append(entry)

        except (ValueError, IndexError):
            continue

    return filtered


def print_results(results, header="Results"):
    """
    Допоміжний метод для гарного виводу списку результатів.
    """
    print(f"\n=== {header} ===")
    if not results:
        print("No data.")
        return
    for r in results:
        print(f"Interval: {r['Interval']}  |  Transfer: {r['Transfer']}  |  Bitrate: {r['Bitrate']}")


def generate_summary(parsed_results):
    """
    Генерує зведену статистику (Total і Average) по Transfer і Bitrate.
    """
    print("\n=== Summary Statistics ===")
    if not parsed_results:
        print("No intervals to summarize.")
        return

    total_transfer = 0.0
    total_bitrate = 0.0
    count = len(parsed_results)

    for entry in parsed_results:
        try:
            transfer_val = float(entry["Transfer"].split()[0])
            bitrate_val = float(entry["Bitrate"].split()[0])
            total_transfer += transfer_val
            total_bitrate += bitrate_val
        except:
            continue

    average_transfer = total_transfer / count
    average_bitrate = total_bitrate / count

    print(f"Total Transfer: {total_transfer:.2f} MBytes")
    print(f"Average Transfer per Interval: {average_transfer:.2f} MBytes")
    print(f"Average Bitrate: {average_bitrate:.2f} Mbits/sec")


########################################################################
# 3. Основний тестовий сценарій
########################################################################
def main():
    print("=== Starting Automated iPerf Tests ===\n")

    # 1. Ping Test
    ping_ok, ping_output = ping_server(SERVER_IP)
    if not ping_ok:
        print("** Ping Test Failed. Stopping further tests. **\n")
        return

    # 2. TCP Test
    print("\n=== Test 1: TCP Connection Test ===")
    stdout, stderr = run_iperf_client(SERVER_IP, udp=False)
    if stderr and "error" in stderr.lower():
        print(f"TCP Test: FAILED with error: {stderr}")
    else:
        print("Raw Output:")
        print(stdout)
        parsed_results = parse_iperf_output(stdout)
        print_results(parsed_results, "Parsed TCP Results")

        # Фільтрація результатів
        filtered = filter_results(parsed_results)
        print_results(filtered, "Filtered TCP Results (Transfer > 2MB, Bitrate > 20Mbits/sec)")
        if filtered:
            print("TCP Filter Test: PASSED (there is at least one interval above the thresholds).")
        else:
            print("TCP Filter Test: No intervals met the criteria.")

        # Зведена статистика
        generate_summary(parsed_results)

    # 3. Емуляція помилки (неправильний IP)
    print("\n=== Test 2: Simulate Server Error (Wrong IP) ===")
    stdout_err, stderr_err = run_iperf_client("192.168.1.200")  # свідомо неправильна адреса
    if stderr_err and "error" in stderr_err.lower():
        print("Error Simulation: PASSED - Script detected error:")
        print(stderr_err)
    else:
        print("Error Simulation: NEED MANUAL CHECK. No error message received (unexpected).")

    # 4. UDP Test (опційний)
    print("\n=== Test 3: UDP Connection Test ===")
    # Зверніть увагу, що для коректної роботи сервера в UDP-режимі
    # на Kali треба запустити:  iperf3 -s -u
    stdout_udp, stderr_udp = run_iperf_client(SERVER_IP, udp=True)
    if stderr_udp and "error" in stderr_udp.lower():
        print(f"UDP Test: FAILED with error: {stderr_udp}")
    else:
        print("Raw UDP Output:")
        print(stdout_udp)
        parsed_udp = parse_iperf_output(stdout_udp)
        print_results(parsed_udp, "Parsed UDP Results")

        # Фільтрація
        filtered_udp = filter_results(parsed_udp)
        print_results(filtered_udp, "Filtered UDP Results (Transfer > 2MB, Bitrate > 20Mbits/sec)")
        if filtered_udp:
            print("UDP Filter Test: PASSED (there is at least one interval above the thresholds).")
        else:
            print("UDP Filter Test: No intervals met the criteria.")

        generate_summary(parsed_udp)

    print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    main()
