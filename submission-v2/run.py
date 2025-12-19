import pandas as pd
import os
import solver
import time
import sys


def main():
    # Find input file
    files = [f for f in os.listdir('.') if f.endswith('.parquet')]
    if not files:
        files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    if not files:
        files = [f for f in os.listdir('.') if f.endswith('.csv')]

    if not files:
        print("ERROR: No input file found (looking for .parquet, .xlsx, or .csv)")
        return

    target_file = files[0]
    print(f"=" * 60)
    print(f"Running Logic Grid Solver")
    print(f"Input file: {target_file}")
    print(f"=" * 60)

    # Load data
    try:
        if target_file.endswith('.parquet'):
            df = pd.read_parquet(target_file)
        elif target_file.endswith('.xlsx'):
            df = pd.read_excel(target_file)
        else:
            df = pd.read_csv(target_file)
    except Exception as e:
        print(f"ERROR: Failed to load file: {e}")
        return

    print(f"Loaded {len(df)} puzzles")
    print()

    results = []
    total_steps = 0
    solved_count = 0
    start_time = time.time()

    # Process each puzzle
    for idx, row in df.iterrows():
        pid = row.get('id', str(idx))
        text = row.get('puzzle') or row.get('clues') or row.get('inputs') or str(row)

        try:
            grid_json, steps = solver.solve_puzzle(str(text), pid)
            results.append([pid, grid_json, steps])
            total_steps += steps

            # Count as solved if we got a non-empty grid
            import json
            parsed = json.loads(grid_json)
            if parsed.get('rows') and any(any(cell for cell in row[1:]) for row in parsed['rows']):
                solved_count += 1

            # Progress indicator
            if (idx + 1) % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / (idx + 1)
                remaining = (len(df) - idx - 1) * avg_time
                print(f"Progress: {idx + 1}/{len(df)} puzzles ({solved_count} solved, "
                      f"avg {total_steps / (idx + 1):.2f} steps, "
                      f"ETA: {remaining:.1f}s)")
                sys.stdout.flush()

        except Exception as e:
            print(f"ERROR on puzzle {pid}: {e}")
            results.append([pid, '{"header": ["House"], "rows": []}', 0])

    end_time = time.time()
    avg_steps = total_steps / len(df) if len(df) > 0 else 0

    # Summary
    print()
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total Puzzles:        {len(df)}")
    print(f"Successfully Solved:  {solved_count} ({100 * solved_count / len(df):.1f}%)")
    print(f"Total Time:           {end_time - start_time:.2f}s")
    print(f"Avg Time per Puzzle:  {(end_time - start_time) / len(df):.3f}s")
    print(f"Total Steps:          {total_steps}")
    print(f"Average Steps:        {avg_steps:.2f}")
    print(f"Zero-Step Solves:     {sum(1 for r in results if r[2] == 0)}")
    print("=" * 60)

    # Estimate score (rough approximation)
    # Score = Accuracy - 10 * (AvgSteps / MaxAvgSteps)
    # Assuming MaxAvgSteps ~ 10 for conservative estimate
    accuracy = solved_count / len(df) if len(df) > 0 else 0
    est_score = accuracy - 10 * (avg_steps / 10.0)
    print(f"Estimated Score:      {est_score:.4f}")
    print(f"  (Accuracy: {accuracy:.4f}, Step Penalty: {10 * avg_steps / 10.0:.4f})")
    print("=" * 60)

    # Save results
    output_df = pd.DataFrame(results, columns=['id', 'grid_solution', 'steps'])
    output_df.to_csv('results_test.csv', index=False)
    print()
    print("✓ Results saved to results_test.csv")
    print()


if __name__ == '__main__':
    main()