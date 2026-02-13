import subprocess
import sys
import argparse
import os
"""
шаблон

"1": {
   "user": "u",
   "ip": "ip",
   "port": 1,
   "key_file": path/to/key_file,
   "password": "p",
},

"""
# конфигурация
SSH_CONFIG = {
    "1": {
        "user": "ubuntu",
        "ip": "192.168.0.0.1",
        "port": 22,
        "key_file": None,
        "password": "qwerty123",
    },
    "2": {
        "user": "root",
        "ip": "192.168.0.0.1",
        "port": 22,
        "key_file": None,
        "password": None,
    },
"local": {
    "user": "arch",
    "ip": "192.168.0.0.1",
    "port": 22,
    "key_file": None,
    "password": None,
},
}

def execute_ssh(user, ip, command=None, port=22, key_file=None, password=None):
    """
    Выполнить SSH команду с дополнительными параметрами

    Args:
        user:  имя пользователя
        ip: IP адрес или хостнейм
        command: команда для выполнения
        port:    порт SSH (по умолчанию 22)
        key_file: путь к приватному ключу
        password: пароль для аутентификации
    """

    # Проверка sshpass для аутентификации по паролю
    if password:
        try:
            subprocess.run(["sshpass", "-V"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(" Ошибка: sshpass не установлен!")
            print("Установите его:")
            print("  Arch Linux: sudo pacman -S sshpass")
            print("  Debian/Ubuntu: sudo apt install sshpass")
            print("  Fedora: sudo dnf install sshpass")
            return False

    ssh_parts = ["ssh"]

    # Добавить параметры для автоматического принятия ключа хоста
    ssh_parts.append("-o StrictHostKeyChecking=no")
    ssh_parts.append("-o UserKnownHostsFile=/dev/null")
    ssh_parts.append("-o ConnectTimeout=10")

    # Добавить порт если не стандартный
    if port != 22:
        ssh_parts.append(f"-p {port}")

    # Добавить приватный ключ если указан
    if key_file and os.path.exists(key_file):
        ssh_parts.append(f"-i {key_file}")
    elif key_file:
        print(f" Предупреждение: ключ не найден {key_file}")

    # Учетные данные сервера
    ssh_parts.append(f"{user}@{ip}")

    # Добавить команду если нужна
    if command:
        ssh_parts.append(f'"{command}"')

    ssh_command = " ".join(ssh_parts)

    try:
        print(f" Подключение к {user}@{ip}:{port}")
        if key_file:
            print(f" Аутентификация:  ключ SSH")
        elif password:
            print(f" Аутентификация: пароль")
        print(f" Команда: {ssh_command}\n")

        # Если есть пароль используем sshpass
        if password:
            full_command = f'sshpass -p "{password}" {ssh_command}'
            result = subprocess.run(full_command, shell=True)
        else:
            result = subprocess.run(ssh_command, shell=True)

        if result.returncode == 0:
            print("\n✓ Успешно выполнено")
        else:
            print(f"\n✗ Ошибка подключения (код: {result.returncode})")

        return result.returncode == 0

    except Exception as e:
        print(f" Ошибка:    {e}")
        return False


def list_servers():
    """Вывести список всех доступных серверов"""
    print("\n Доступные серверы:")
    print("-" * 70)
    for name, config in SSH_CONFIG.items():
        if config["key_file"]:
            auth_info = " ключ SSH"
        elif config["password"]:
            auth_info = " пароль"
        else:
            auth_info = " не настроено"

        print(
            f"  {name:15} | {config['user']}@{config['ip']:10} | {config['port']:4} | {auth_info}"
        )
    print("-" * 70 + "\n")


def interactive_mode():
    """Интерактивный режим выбора сервера"""
    list_servers()

    server_name = input(
        "Выберите сервер из списка (или введите 'custom' для ручного ввода): "
    ).strip()

    if server_name == "custom":
        user = input("Имя пользователя:  ")
        ip = input("IP адрес или хостнейм: ")
        port = input("Порт (по умолчанию 22): ") or "22"

        print("\nВыберите тип аутентификации:")
        print("  1 - SSH ключ")
        print("  2 - Пароль")
        print("  3 - Интерактивный ввод (без автоматизации)")

        auth_choice = input("Выбор (1/2/3): ").strip()

        key_file = None
        password = None

        if auth_choice == "1":
            key_file = input("Путь к SSH ключу: ")
        elif auth_choice == "2":
            password = input("Пароль: ")

        config = {
            "user": user,
            "ip": ip,
            "port": int(port),
            "key_file": key_file,
            "password": password,
        }
    elif server_name in SSH_CONFIG:
        config = SSH_CONFIG[server_name]
    else:
        print(f" Сервер '{server_name}' не найден")
        return

    command = (
        input("Введите команду (или оставьте пусто для интерактивной сессии): ").strip()
        or None
    )

    execute_ssh(
        user=config["user"],
        ip=config["ip"],
        command=command,
        port=config["port"],
        key_file=config["key_file"],
        password=config["password"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SSH клиент с предустановленными конфигурациями и автоматическим вводом пароля",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:  
  python ssh_cli_configured.py                    # Интерактивный режим
  python ssh_cli_configured.py -ls                # Список серверов
  python ssh_cli_configured.py -s server1         # Подключение к server1
  python ssh_cli_configured.py -s server1 -c "ls -la"  # Выполнить команду
  python ssh_cli_configured.py -u admin -i 192.168.1.100 -pw "пароль"  # С паролем
  python ssh_cli_configured.py -u admin -i 192.168.1.100 -k /path/to/key  # С ключом
        """,
    )

    parser.add_argument(
        "-ls",
        "--list-servers",
        action="store_true",
        help="Показать список доступных серверов",
    )
    parser.add_argument("-s", "--server", help="Имя сервера из конфигурации")
    parser.add_argument("-u", "--user", help="Имя пользователя")
    parser.add_argument("-i", "--ip", help="IP адрес или хостнейм")
    parser.add_argument(
        "-p", "--port", type=int, default=22, help="Порт SSH (по умолчанию 22)"
    )
    parser.add_argument("-k", "--key", help="Путь к приватному ключу")
    parser.add_argument("-c", "--command", help="Команда для выполнения")
    parser.add_argument("-pw", "--password", help="Пароль для аутентификации")

    args = parser.parse_args()

    # Показать список серверов
    if args.list_servers:
        list_servers()
        sys.exit(0)

    # Подключение к предустановленному серверу
    if args.server:
        if args.server in SSH_CONFIG:
            config = SSH_CONFIG[args.server]
            execute_ssh(
                user=config["user"],
                ip=config["ip"],
                command=args.command,
                port=config["port"],
                key_file=config["key_file"],
                password=config["password"],
            )
        else:
            print(f" Сервер '{args.server}' не найден")
            list_servers()

    # Ручное подключение с параметрами
    elif args.user and args.ip:
        execute_ssh(
            user=args.user,
            ip=args.ip,
            command=args.command,
            port=args.port,
            key_file=args.key,
            password=args.password,
        )

    # Интерактивный режим ��о умолчанию
    else:
        interactive_mode()
