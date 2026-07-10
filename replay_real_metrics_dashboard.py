from engine.replay_real_metrics_evaluator import run

def main():
    result=run()
    print("="*90)
    print("🧪 Freakto Replay Real Metrics Evaluator v10.1.3")
    print("="*90)
    for k,v in result.items():
        print(f"{k}: {v}")

if __name__=="__main__":
    main()
