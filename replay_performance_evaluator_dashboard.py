"""Freakto Replay Performance Evaluator Dashboard v10.1.2"""

from engine.replay_performance_evaluator import run

def main():
    result = run()
    print("=" * 90)
    print("🧪 Freakto Replay Performance Evaluator v10.1.2")
    print("=" * 90)

    for key, value in result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
