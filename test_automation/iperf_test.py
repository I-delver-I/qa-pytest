import pytest
import parser

class TestSuite():
    def test_iperf3_client_connection(self, client):
        """
        Переконуємося, що:
        1) Немає помилки під час підключення (stderr порожній, немає 'error' у виводі).
        2) Парсимо stdout та перевіряємо, що Transfer > 2 MB і Bitrate > 20 Mbits/sec
           принаймні в одному з інтервалів.
        """
        stdout, stderr, error_serv = client

        print("\n> Received from fixture client is:\n", stdout)

        # 1) Перевірка помилок
        assert not error_serv, f"Server error found: {error_serv}"
        assert not stderr, f"Client stderr is not empty: {stderr}"

        # 2) Парсимо вивід
        dict_data = parser.parser(stdout)
        
        for item in dict_data:
            print(item)

        # 3) Логіка перевірки (Transfer > 2.0 Мбайт і Bitrate > 20.0 Мбіт/с)
        found_ok = False
        for value in dict_data:
            transfer_parts = value["Transfer"].split()
            bitrate_parts = value["Bitrate"].split()

            if len(transfer_parts) == 2 and len(bitrate_parts) == 2:
                transfer_val = float(transfer_parts[0])
                transfer_unit = transfer_parts[1]  # "MBytes", "KBytes", etc.
                
                bitrate_val = float(bitrate_parts[0])
                bitrate_unit = bitrate_parts[1]  # "Mbits/sec", "Kbits/sec", etc.

                if "KBytes" in transfer_unit:
                    transfer_val /= 1024.0
                elif "GBytes" in transfer_unit:
                    transfer_val *= 1024.0

                if "Kbits/sec" in bitrate_unit:
                    bitrate_val /= 1024.0
                elif "Gbits/sec" in bitrate_unit:
                    bitrate_val *= 1024.0

                if transfer_val > 2.0 and bitrate_val > 20.0:
                    found_ok = True
                    break
        
        assert found_ok, "No intervals had Transfer > 2 MB AND Bitrate > 20 Mbits/sec!"
