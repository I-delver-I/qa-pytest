import re

REGEXP = r"\[\s*\d+\]\s+([\d\.\-]+)\-([\d\.\-]+)\s+sec\s+([\d\.]+)\s+([MGK]?Bytes)\s+([\d\.]+)\s+([MGK]?bits/sec)\s+(\d+)\s+([\d\.]+)\s+([KMG]?Bytes)"

def parser(iperf_output):
    """
    Повертає список словників, у кожному з яких збережені
    'Interval', 'Transfer', 'Bitrate', 'Retr', 'Cwnd' (залежно від того,
    що ми хочемо вичитати з виводу iperf).
    """
    matches = re.findall(REGEXP, iperf_output)
    results = []

    for m in matches:
        start_time = m[0]
        end_time = m[1]
        transfer_val = m[2]
        transfer_unit = m[3]
        bitrate_val = m[4]
        bitrate_unit = m[5]
        retr = m[6]
        cwnd_val = m[7]
        cwnd_unit = m[8]

        # Формуємо "інтервал"
        interval_str = f"{start_time}-{end_time} sec"

        # Формуємо словник з потрібних полів
        data_dict = {
            "Interval": interval_str,
            "Transfer": f"{transfer_val} {transfer_unit}",
            "Bitrate":  f"{bitrate_val} {bitrate_unit}",
            "Retr":     retr,
            "Cwnd":     f"{cwnd_val} {cwnd_unit}"
        }

        results.append(data_dict)

    return results