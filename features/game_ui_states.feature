Feature: Game State Management and UI
  As a player
  I want intuitive game states and user interface
  So I can understand game objectives and progress

  Scenario: Game startup and main menu
    Given the game is launched
    When the application starts
    Then the main menu should be displayed
    And the game world should not be rendered
    And music should play in background

  Scenario: Starting a new game
    Given I'm in main menu
    When I click 'Start Game'
    Then the game world should load
    And the player should be positioned at spawn point
    And the game state should change to 'playing'

  Scenario: Player death and game over
    Given my health reaches 0
    When I take final damage
    Then the game should transition to game over state
    And a game over screen should be displayed
    And I should have option to restart or return to menu

  Scenario: Pause menu functionality
    Given the game is running
    When I press 'Escape' key
    Then the game should pause
    And the pause menu should overlay the game view
    And all game time should stop

  Scenario: Objective tracking and progression
    Given I need to hunt 3 deer for objective
    When I successfully kill a deer
    Then the objective counter should update (2/3 remaining)
    And a notification should appear in HUD
    And I should feel satisfaction from progress

  Scenario: Health and stamina display
    Given I'm injured from animal attack
    When I take damage
    Then the health bar should decrease visually
    And the screen should show red tint effect
    And I should hear injured audio cue

  Scenario: Weapon and ammo UI
    Given I'm low on ammunition
    When I check my weapon
    Then the ammo counter should show '1/30'
    And the reload button should be highlighted
    And I should see remaining magazine count

  Scenario: Minimap and navigation
    Given I'm exploring new area
    When I look at minimap
    Then the minimap should show my position
    And nearby animals should be marked as icons
    And terrain features should be visible

  Scenario: Weather and environment display
    Given it starts raining
    When weather changes occur
    Then the sky should show rain clouds
    And the minimap should indicate weather
    And animal behavior should change (animals seek shelter)

  Scenario: Sound and audio feedback
    Given I shoot a weapon
    When the gunshot happens
    Then the sound should play with distance attenuation
    And nearby animals should react to the noise
    And an echo effect should occur in mountains

  Scenario: Hunting success celebration
    Given I complete the main objective
    When I kill the final required animal
    Then a victory screen should appear
    And celebratory music should play
    And my score should be displayed with statistics

  Scenario: Settings and options
    Given I want to adjust graphics quality
    When I access settings menu
    Then I should see sliders for graphics options
    And changes should apply immediately
    And I should be able to revert changes before exiting

  Scenario: Control scheme customization
    Given I want to remap controls
    When I access control settings
    Then I should see all current key bindings
    And I should be able to click and press new keys
    And the changes should save to configuration
