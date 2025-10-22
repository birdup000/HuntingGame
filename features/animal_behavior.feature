Feature: Animal Spawning and Behavior
  As a game system
  I want to spawn animals with intelligent behavior patterns
  So the player has realistic hunting targets

  Scenario: Deer spawning in valid locations
    Given the game is initializing
    When the system spawns deer in the environment
    Then deer should be positioned on terrain height
    And deer should be at least 10 meters from player spawn point
    And deer should have random initial states (IDLE, FORAGING, ALERTED)

  Scenario: Rabbit spawning with terrain validation
    Given the game is initializing
    When the system spawns rabbits
    Then rabbits should be positioned on terrain height with proper offset
    And rabbits should avoid steep slopes (>60 degrees)
    And rabbits should be within forest biome boundaries

  Scenario: Animal state transitions from IDLE to ALERTED
    Given a deer is in IDLE state
    When the player comes within 30 meters detection range
    Then the deer should transition to ALERTED state
    And the deer should turn to face the player direction
    And the deer should pause movement for 2 seconds

  Scenario: Animal fleeing from player
    Given a deer is in ALERTED state
    When the player gets closer than 15 meters
    Then the deer should transition to FLEEING state
    And the deer should move away from player at maximum speed
    And the deer should choose escape path avoiding obstacles

  Scenario: Animal foraging behavior
    Given a rabbit is in FORAGING state
    When the rabbit is not detecting threats
    Then the rabbit should move randomly within small radius (5m)
    And the rabbit should occasionally stop to 'eat'
    And the rabbit should remain in FORAGING state for 3-7 seconds

  Scenario: Animal detection range validation
    Given a deer is in IDLE state
    When the player moves around the deer
    Then the deer should only detect when player is within 50m radius
    And detection should be affected by wind direction
    And dense vegetation should reduce detection range by 20%

  Scenario: Animal pathfinding around obstacles
    Given an animal is fleeing from player
    When there's a river between animal and escape direction
    Then the animal should find path around river
    And the animal should not get stuck on terrain features
    And the animal should reach minimum safe distance (50m) from player

  Scenario: Animal spawning with population limits
    Given the game has spawned 20 deer maximum
    When trying to spawn additional deer
    Then the system should not exceed population limit
    And existing animals should be checked for valid spawn positions
    And spawn attempts should have failsafe after 1000 attempts

  Scenario: Animal health and injury behavior
    Given a deer is hit by player projectile
    Then the deer should transition to FLEEING state if not killed
    And the deer should leave blood trail visual effects
    And the deer movement speed should decrease by 30%

  Scenario: Animal death and removal
    Given an animal's health reaches 0
    Then the animal should transition to DEAD state
    And the animal should stop moving
    And the animal collision detection should be disabled after 10 seconds
