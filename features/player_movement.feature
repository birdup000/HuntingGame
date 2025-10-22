Feature: Player Movement and Controls
  As a player
  I want to control my character's movement and camera
  So I can navigate the hunting environment

  Scenario: Basic WASD movement on flat terrain
    Given the game is running and player is in playing state
    When I press the 'W' key for 1 second
    Then the player should move forward from their starting position
    And the camera should follow the player movement

  Scenario: Strafing movement with 'A' and 'D' keys
    Given the player is stationary on flat terrain
    When I press the 'A' key for 0.5 seconds
    Then the player should move to the left
    And the player's orientation should rotate to face the movement direction

  Scenario: Backward movement with 'S' key
    Given the player is facing north
    When I press the 'S' key
    Then the player should move backward
    And the player's orientation should remain facing north

  Scenario: Camera rotation with mouse movement
    Given the player is stationary
    When I move the mouse to the right
    Then the camera should rotate to the right
    And the player's view direction should change accordingly

  Scenario: Crouching with 'C' key
    Given the player is standing
    When I press the 'C' key
    Then the player's height should decrease
    And the camera should move closer to the ground
    And the movement speed should be reduced by 50%

  Scenario: Jumping with spacebar
    Given the player is on flat terrain
    When I press the spacebar
    Then the player should move upward
    And gravity should pull the player back down to the terrain height

  Scenario: Movement speed based on stamina
    Given the player has low stamina
    When I try to move forward
    Then the movement speed should be reduced
    And the stamina should decrease faster

  Scenario: Movement on sloped terrain
    Given the player is on a hill with 45-degree slope
    When I try to move uphill
    Then the movement speed should be reduced
    And the player should follow the terrain elevation

  Scenario: Collision with environment objects
    Given the player is moving forward
    When the player collides with a rock
    Then the player should stop moving forward
    And the movement input should be ignored until directional change

  Scenario: Camera collision avoidance
    Given the camera is behind the player
    When the camera would clip through a wall
    Then the camera should move closer to the player
    And the field of view should remain unobstructed
