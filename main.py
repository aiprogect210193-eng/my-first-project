"""
Точка входа — диалоговый интерфейс с агентом.
Запуск: python main.py
"""
import sys
import os

# Проверяем наличие .env
if not os.path.exists(".env"):
    print("⚠️  Файл .env не найден.")
    print("   Скопируйте .env.example → .env и заполните API-ключи.")
    sys.exit(1)

from agent.loop import AgentLoop

BANNER = """
╔═══════════════════════════════════════════════════════╗
║       Маркетинговый ИИ агент — Яндекс Директ         ║
╠═══════════════════════════════════════════════════════╣
║  Команды:                                             ║
║    /reset    — сбросить историю разговора             ║
║    /report   — запустить полный цикл + отчёт          ║
║    /web      — запустить веб-платформу (порт 8000)    ║
║    /exit     — выход                                  ║
╚═══════════════════════════════════════════════════════╝
"""


def start_web():
    import subprocess
    print("Запускаю веб-платформу на http://localhost:8000 ...")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("Платформа запущена. Откройте http://localhost:8000 в браузере.")


def main():
    print(BANNER)

    try:
        agent = AgentLoop()
    except Exception as e:
        print(f"❌ Ошибка инициализации агента: {e}")
        print("   Проверьте ANTHROPIC_API_KEY в файле .env")
        sys.exit(1)

    print("Агент готов. Опишите задачу на русском или английском языке.\n")

    while True:
        try:
            user_input = input("Вы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nДо свидания!")
            break

        if not user_input:
            continue

        # Встроенные команды
        if user_input == "/exit":
            print("До свидания!")
            break
        elif user_input == "/reset":
            agent.reset()
            print("История разговора сброшена.")
            continue
        elif user_input == "/web":
            start_web()
            continue
        elif user_input == "/report":
            print("Запускаю еженедельный цикл оптимизации и формирую отчёт...")
            try:
                from automation.weekly_cycle import run_weekly_cycle
                report = run_weekly_cycle()
                print(f"\n{report}")
            except Exception as e:
                print(f"Ошибка: {e}")
            continue

        # Обычный диалог с агентом
        print("\nАгент: ", end="", flush=True)
        try:
            response = agent.run(user_input)
            print(response)
        except Exception as e:
            print(f"Ошибка агента: {e}")
        print()


if __name__ == "__main__":
    main()
