# BDD Testing Guide for 3D Hunting Simulator

## Overview

This guide explains how to use the Behavior-Driven Development (BDD) testing framework integrated with the 3D Hunting Simulator project.

## Quick Start

### 1. Install BDD Dependencies
```bash
pip install -r requirements-bdd.txt
```

### 2. Run BDD Tests
```bash
# Run all BDD tests
python run_bdd_tests.py

# Run specific feature
pytest features/player_movement.feature -v

# Run with coverage
pytest features/ --cov=core --cov=player --cov=animals --cov=physics --cov=environment
```

### 3. Add New Features
1. Create new `.feature` file in `features/` directory
2. Write Gherkin scenarios using Given/When/Then syntax
3. Implement step definitions in `features/step_definitions/`
4. Run tests to verify implementation

## Feature Files Structure

```
features/
├── player_movement.feature      # Player controls and movement
├── animal_behavior.feature      # Animal AI and spawning  
├── combat_system.feature        # Weapons and combat mechanics
├── game_ui_states.feature       # UI, menus, and game states
└── environment_terrain.feature  # Environment and terrain systems
```

## Writing Features

### Basic Gherkin Syntax
```gherkin
Feature: [Feature Name]
  As a [user role]
  I want to [functionality] 
  So I can [business value]

  Scenario: [Scenario Name]
    Given [context/preconditions]
    When [action/step]
    Then [expected outcome]
```

### Example Feature
```gherkin
Feature: Player Movement and Controls
  As a player
  I want to control my character's movement and camera
  So I can navigate the hunting environment

  Scenario: Basic WASD movement on flat terrain
    Given the game is running and player is in playing state
    When I press the 'W' key for 1 second
    Then the player should move forward from their starting position
```

## Step Definitions

Step definitions implement the Gherkin scenarios in Python code.

### Location
```
features/
└── step_definitions/
    └── hunt_steps.py
```

### Basic Structure
```python
from pytest_bdd import given, when, then
import pytest

@pytest.fixture
def game_app():
    """Create test fixture."""
    app = Mock()
    return app

@given('the game is running and player is in playing state')
def game_running_playing(mock_game):
    mock_game.is_running = True
    mock_game.game_state = 'playing'

@when('I press the \'W\' key for 1 second')
def press_w_key(mock_player):
    # Implementation logic
    pass

@then('the player should move forward from their starting position')
def player_moved_forward(mock_player):
    assert mock_player.moved_forward
```

## Running Tests

### Command Options
```bash
# All BDD tests with verbose output
pytest features/ -v

# Specific feature
pytest features/player_movement.feature -v

# With coverage reporting
pytest features/ --cov=core --cov-report=html

# Parallel execution (faster)
pytest features/ -n 4

# Only failed tests
pytest features/ --lf

# Stop on first failure
pytest features/ -x
```

### Test Report Configuration
- HTML coverage reports: `htmlcov_bdd/`
- Console output: Inline test results
- Integration with existing TDD tests: Automatic

## Integration with Existing Tests

The BDD framework integrates seamlessly with existing TDD tests:

1. **Shared Fixtures**: Use common mock objects and test data
2. **Combined Coverage**: Both TDD and BDD tests contribute to overall coverage
3. **Unified Reporting**: Comprehensive test summary with both approaches

### Example Integration
```python
# In tdd_comprehensive_tests.py
try:
    from features.step_definitions.hunt_steps import *
    BDD_AVAILABLE = True
except ImportError:
    BDD_AVAILABLE = False
```

## Best Practices

### Writing Effective Scenarios
1. **Focus on Behavior**: Test user-visible functionality, not implementation
2. **Use Business Language**: Write scenarios in domain language
3. **Keep Scenarios Independent**: Each scenario should be runnable alone
4. **Test One Thing**: Each scenario should test one specific behavior

### Maintaining Step Definitions
1. **Reuse Steps**: Share common steps across scenarios
2. **Use Fixtures**: Extract common setup into pytest fixtures
3. **Keep Steps Focused**: Each step should do one clear action
4. **Handle Edge Cases**: Include negative test scenarios

### Common Patterns

#### State Management
```gherkin
Given the player has full health
And the player has 30 bullets
When the player shoots at a deer
Then the player should have 29 bullets
```

#### Error Conditions  
```gherkin
Given the player has 0 bullets
When the player tries to shoot
Then the shot should fail
And a reload prompt should appear
```

#### Integration Testing
```gherkin
Given a deer is grazing in forest
When the player shoots from 50m distance
And the bullet hits the deer
Then the deer should flee
And the player should hear the impact sound
```

## Advanced Features

### Scenario Outlines (Data-Driven Testing)
```gherkin
Scenario Outline: Different weapon types
  Given I have a <weapon_type>
  When I shoot at a target
  Then the damage should be <expected_damage>

  Examples:
    | weapon_type | expected_damage |
    | Rifle       | 25            |
    | Shotgun     | 50            |
    | Pistol      | 15            |
```

### Background Sections
```gherkin
Feature: Animal Spawning
  Background:
    Given the game world is generated
    And the player is at position (0, 0, 0)
    
  Scenario: Deer spawns nearby
    When a deer spawns
    Then it should be at least 10m from player
```

## Troubleshooting

### Common Issues

**Step Not Found**
```
Could not find step definition for: "Given ..."
```
Solution: Check step definition exists and spelling matches exactly

**Test Failing Unexpectedly**
```
Assertion error: Expected X, got Y
```
Solution: Verify the implementation matches the behavior specification

**Import Errors**
```
ModuleNotFoundError: No module named 'pytest_bdd'
```
Solution: Install dependencies with `pip install -r requirements-bdd.txt`

### Debugging Tips

1. **Run Single Test**: `pytest features/player_movement.feature::scenario -v`
2. **Check Fixtures**: Verify test fixtures are set up correctly
3. **Use Debug Mode**: Add `pdb.set_trace()` or print statements
4. **Review Coverage**: Check which code paths are tested

## Continuous Integration

### GitHub Actions Integration
```yaml
- name: Run BDD Tests
  run: |
    pip install -r requirements-bdd.txt
    python run_bdd_tests.py
```

### Coverage Reporting
- HTML reports in `htmlcov_bdd/`
- Integration with existing CI/CD pipelines
- Quality gates for minimum coverage requirements

## Contributing

When adding new features:

1. **Write Scenarios First**: Define behavior before implementation
2. **Test Edge Cases**: Include error conditions and boundary values
3. **Update Documentation**: Keep this guide current
4. **Review Coverage**: Ensure new code is properly tested

## Support

For issues with the BDD framework:

1. Check this guide for common solutions
2. Run `python run_bdd_tests.py` for system diagnostics
3. Verify all dependencies are installed
4. Check that feature files are in the correct location

---

**Key Benefits Achieved:**
- ✅ Clear behavioral specifications
- ✅ Integration testing of complex workflows  
- ✅ Living documentation from passing tests
- ✅ Improved communication between team members
- ✅ Comprehensive test coverage of game mechanics
