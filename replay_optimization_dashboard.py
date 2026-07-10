"""Freakto v10.1 Replay Optimization Lab Dashboard."""
from engine.replay_optimizer import run_lab

def main():
    result=run_lab()
    print("="*90)
    print("🧪 Freakto Replay Optimization Lab v10.1.0")
    print("="*90)
    for k,v in result.items():
        print(f"{k}: {v}")

if __name__=="__main__":
    main()
