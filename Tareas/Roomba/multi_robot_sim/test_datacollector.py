"""
Test script to verify DataCollector functionality in multi-robot simulation
This test runs a short simulation and verifies that all metrics are being
collected correctly at each step.
"""

from cleaning_fleet.model import RoombaMultiAgentModel
import pandas as pd


def testDataCollectorIntegration():
    """
    Function: testDataCollectorIntegration
    Purpose: Verify that DataCollector is properly integrated and collecting data
    Parameters: None
    Returns: Boolean indicating test success
    Note: Runs simulation for 50 steps and validates data collection
    """
    print("=" * 60)
    print("TESTING DATACOLLECTOR INTEGRATION")
    print("=" * 60)

    # Create model with moderate parameters
    print("\n[1] Creating model: 3 robots, 10x10 grid, 15 dirty cells")
    model = RoombaMultiAgentModel(
        num_agents=3,
        width=10,
        height=10,
        num_dirty_cells=15,
        num_obstacles=5,
        max_steps=100,
        seed=42
    )

    print(f"    ✓ Model created successfully")
    print(f"    - Total robots: {len(model.cleaners)}")
    print(f"    - Total docks: {len(model.allDocks)}")
    print(f"    - Initial dirt: {model.remaining_dirt}")

    # Run simulation for 50 steps
    print("\n[2] Running simulation for 50 steps...")
    stepsToRun = 50
    for step in range(stepsToRun):
        model.step()
        if not model.running:
            print(f"    ℹ Simulation ended early at step {step + 1}")
            break

    print(f"    ✓ Simulation completed")

    # Extract collected data
    print("\n[3] Analyzing collected data...")
    dataframe = model.datacollector.get_model_vars_dataframe()

    # Validation checks
    testPassed = True

    # Check 1: Data was collected
    if len(dataframe) == 0:
        print("    ✗ FAIL: No data collected!")
        testPassed = False
    else:
        print(f"    ✓ Collected {len(dataframe)} data points")

    # Check 2: All expected columns present
    expectedColumns = [
        "RemainingDirt", "TotalSteps", "AverageEnergy", "MinEnergy",
        "MaxEnergy", "RobotsCharging", "DocksOccupied", "DocksAvailable",
        "RobotsLowEnergy", "CleaningProgress"
    ]

    missingColumns = [col for col in expectedColumns if col not in dataframe.columns]
    if missingColumns:
        print(f"    ✗ FAIL: Missing columns: {missingColumns}")
        testPassed = False
    else:
        print(f"    ✓ All {len(expectedColumns)} expected metrics present")

    # Check 3: Data values are reasonable
    if len(dataframe) > 0:
        # Energy should be between 0 and 100
        if dataframe["AverageEnergy"].min() < 0 or dataframe["AverageEnergy"].max() > 100:
            print("    ✗ FAIL: Invalid energy values detected")
            testPassed = False
        else:
            print("    ✓ Energy values within valid range [0, 100]")

        # Progress should increase or stay constant
        progressValues = dataframe["CleaningProgress"].values
        if not all(progressValues[i] <= progressValues[i+1] for i in range(len(progressValues)-1)):
            print("    ✗ FAIL: Cleaning progress decreased (should be monotonic)")
            testPassed = False
        else:
            print("    ✓ Cleaning progress is monotonically increasing")

        # Remaining dirt should decrease or stay constant
        dirtValues = dataframe["RemainingDirt"].values
        if not all(dirtValues[i] >= dirtValues[i+1] for i in range(len(dirtValues)-1)):
            print("    ✗ FAIL: Remaining dirt increased (should be monotonic decreasing)")
            testPassed = False
        else:
            print("    ✓ Remaining dirt is monotonically decreasing")

    # Display summary statistics
    print("\n[4] Data Summary Statistics:")
    print("-" * 60)
    print(dataframe.describe())

    # Display first and last 5 rows
    print("\n[5] First 5 data points:")
    print("-" * 60)
    print(dataframe.head())

    print("\n[6] Last 5 data points:")
    print("-" * 60)
    print(dataframe.tail())

    # Test result
    print("\n" + "=" * 60)
    if testPassed:
        print("✓ TEST PASSED: DataCollector is working correctly!")
        print("  All metrics are being collected and values are valid.")
    else:
        print("✗ TEST FAILED: Issues detected with DataCollector")
    print("=" * 60)

    return testPassed


def testDataExport():
    """
    Function: testDataExport
    Purpose: Verify that collected data can be exported to CSV
    Parameters: None
    Returns: Boolean indicating test success
    """
    print("\n\n")
    print("=" * 60)
    print("TESTING DATA EXPORT FUNCTIONALITY")
    print("=" * 60)

    # Create and run short simulation
    print("\n[1] Creating and running test simulation...")
    model = RoombaMultiAgentModel(
        num_agents=2,
        width=8,
        height=8,
        num_dirty_cells=10,
        num_obstacles=3,
        max_steps=30,
        seed=123
    )

    for step in range(30):
        model.step()
        if not model.running:
            break

    print(f"    ✓ Simulation completed after {model.stepCounter} steps")

    # Test CSV export
    print("\n[2] Testing CSV export...")
    try:
        dataframe = model.datacollector.get_model_vars_dataframe()
        csvPath = "/tmp/roomba_test_data.csv"
        dataframe.to_csv(csvPath)
        print(f"    ✓ Data exported successfully to {csvPath}")

        # Verify file exists and has content
        import os
        if os.path.exists(csvPath):
            fileSize = os.path.getsize(csvPath)
            print(f"    ✓ File verified: {fileSize} bytes")
            return True
        else:
            print("    ✗ FAIL: Export file not found")
            return False

    except Exception as e:
        print(f"    ✗ FAIL: Export error: {e}")
        return False


if __name__ == "__main__":
    print("\n\n")
    print("#" * 60)
    print("# DATACOLLECTOR VALIDATION TEST SUITE")
    print("#" * 60)

    # Run integration test
    integrationPassed = testDataCollectorIntegration()

    # Run export test
    exportPassed = testDataExport()

    # Summary
    print("\n\n")
    print("#" * 60)
    print("# TEST SUMMARY")
    print("#" * 60)
    print(f"Integration Test: {'PASSED ✓' if integrationPassed else 'FAILED ✗'}")
    print(f"Export Test: {'PASSED ✓' if exportPassed else 'FAILED ✗'}")

    if integrationPassed and exportPassed:
        print("\n🎉 ALL TESTS PASSED - DataCollector ready for use!")
    else:
        print("\n⚠️  SOME TESTS FAILED - Review implementation")

    print("#" * 60)
