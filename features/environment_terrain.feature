Feature: Environment and Terrain System
  As a player
  I want immersive and interactive environments
  So I can experience realistic hunting scenarios

  Scenario: Procedural terrain generation
    Given the game is starting
    When the environment loads
    Then varied terrain should generate with hills and valleys
    And different biomes should create distinct areas
    And the terrain should be suitable for animal spawning

  Scenario: Terrain height validation for player
    Given the player moves across the map
    When the player position changes
    Then the player should stay at proper height above terrain
    And the player should not clip through the ground
    And movement should account for slope angles

  Scenario: Animal positioning on terrain
    Given animals spawn in the environment
    When an animal is created
    Then the animal should be positioned at terrain height
    And animals should have proper height offset
    And animals should not float above or sink into terrain

  Scenario: Weather system effects
    Given it's currently sunny
    When weather changes to storm
    Then lightning should flash in the sky
    And rain should start falling with sound effects
    And animal behavior should change (seek shelter)

  Scenario: Time of day progression
    Given it's currently noon
    When time progresses to evening
    Then the sky should change colors (orange, purple)
    And shadows should lengthen
    And animal activity should increase (crepuscular behavior)

  Scenario: Biome-based animal spawning
    Given different terrain types exist
    When animals spawn
    Then deer should prefer forest edge areas
    And rabbits should spawn in meadow areas
    And spawning should respect biome boundaries

  Scenario: Dynamic lighting changes
    Given the sun position changes
    When transitioning from day to night
    Then lighting should gradually dim
    And artificial lights should turn on (if any)
    And visibility should decrease for player

  Scenario: Grass and foliage interaction
    Given I walk through tall grass
    When the player moves
    Then grass should bend around player feet
    And sound should indicate movement through vegetation
    And animals should leave different tracks in grass

  Scenario: Water body interactions
    Given there are rivers and lakes
    When animals approach water
    Then animals should drink from water sources
    And water should have realistic reflections
    And player movement should slow in water

  Scenario: Seasonal variations
    Given the game has seasonal system
    When season changes to winter
    Then terrain should show snow coverage
    And animal fur should appear thicker
    And footprints should show in snow

  Scenario: Interactive environment objects
    Given there are rocks and trees
    When I interact with environment
    Then I should be able to hide behind large rocks
    And trees should provide cover from animal detection
    And environment should affect sound propagation

  Scenario: Ecosystem balance simulation
    Given predators exist in the environment
    When prey animals are overhunted
    Then predator populations should decrease
    And new animal spawns should favor different species
    And the ecosystem should show balance effects

  Scenario: Realistic sky and atmosphere
    Given I look at the sky
    When observing sky conditions
    Then clouds should move with wind
    And sky colors should change with weather
    And distant mountains should show atmospheric perspective
