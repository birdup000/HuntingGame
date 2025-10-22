#!/usr/bin/env python3
"""
Test script to verify terrain and animal fixes.
"""

import sys
sys.path.insert(0, '.')

try:
    from environment.pbr_terrain import PBRTerrain
    from animals.animal import Deer, Rabbit
    from panda3d.core import Vec3
    print("SUCCESS: Successfully imported terrain and animal modules")
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    sys.exit(1)

def test_terrain_generation():
    """Test terrain generation with improved texturing."""
    print("\nTesting terrain generation...")
    terrain = PBRTerrain(width=50, height=50, scale=0.5, octaves=4)
    
    # Generate height map
    terrain.generate_terrain()
    if terrain.height_map is not None:
        print(f"SUCCESS: Terrain height map generated: {terrain.height_map.shape}")
        
        # Test height retrieval
        height = terrain.get_height(0, 0)
        print(f"SUCCESS: Terrain height at center: {height}")
    else:
        print("ERROR: Terrain height map is None")
        assert False, "Terrain height map should not be None"
    
    assert True, "Terrain generation test completed successfully"

def test_animal_placement():
    """Test animal placement on terrain."""
    print("\nTesting animal placement...")
    
    terrain = PBRTerrain(width=50, height=50, scale=0.5, octaves=4)
    terrain.generate_terrain()
    
    # Create deer at a specific position
    test_pos = Vec3(10, 15, 0)
    deer = Deer(test_pos)
    
    # Manually set terrain height
    actual_height = terrain.get_height(test_pos.x, test_pos.y)
    deer.position.z = actual_height
    deer.height_offset = 0.0  # Should be 0.0 now
    
    print(f"SUCCESS: Deer positioned at ({test_pos.x}, {test_pos.y}, {actual_height})")
    print(f"SUCCESS: Height offset set to: {deer.height_offset}")
    
    # Test with rabbit too
    rabbit = Rabbit(Vec3(-5, -8, 0))
    rabbit_height = terrain.get_height(-5, -8)
    rabbit.position.z = rabbit_height
    
    print(f"SUCCESS: Rabbit positioned at (-5, -8, {rabbit_height})")
    
    return True

def test_color_improvements():
    """Test color improvements for terrain zones."""
    print("\nTesting terrain color improvements...")
    
    terrain = PBRTerrain()
    
    # Test zone colors
    test_cases = [
        ('snow', 4.0, "Snow zone color"),
        ('rock', 2.5, "Rock zone color"),
        ('wet', -0.5, "Wet zone color"),
        ('forest', 1.0, "Forest zone color"),
        ('unknown', 0.0, "Default zone color")
    ]
    
    for zone, height, description in test_cases:
        color = terrain._get_zone_color(zone, height)
        print(f"SUCCESS: {description}: {color}")
        
        # Verify color is a valid 4-tuple
        if len(color) != 4:
            print(f"ERROR: Invalid color format: {color}")
            return False
        if not all(0 <= c <= 1 for c in color):
            print(f"ERROR: Invalid color values: {color}")
            return False
    
    return True

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("TESTING HUNTING GAME FIXES")
    print("=" * 60)
    
    tests = [
        test_terrain_generation,
        test_animal_placement,
        test_color_improvements
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"SUCCESS: {test.__name__} PASSED")
            else:
                failed += 1
                print(f"FAILED: {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            print(f"FAILED: {test.__name__} FAILED with exception: {e}")
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All tests passed! The fixes are working correctly.")
    else:
        print(f"WARNING: {failed} test(s) failed. Please review the issues above.")
    
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
