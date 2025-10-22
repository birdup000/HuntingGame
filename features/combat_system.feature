Feature: Combat System and Shooting Mechanics
  As a player
  I want to shoot weapons with realistic ballistics
  So I can hunt animals successfully

  Scenario: Basic weapon shooting
    Given the player has a rifle with full ammo
    When I left-click to shoot
    Then a projectile should be created at gun position
    And the projectile should travel in camera direction
    And the ammo count should decrease by 1

  Scenario: Weapon fire rate limiting
    Given I just fired a shot
    When I try to shoot again immediately
    Then the shot should be blocked for 0.5 seconds
    And a visual indicator should show fire rate cooldown

  Scenario: Projectile physics and ballistics
    Given I shoot a bullet horizontally
    Then the bullet should drop due to gravity over distance
    And wind should affect bullet trajectory
    And the bullet should have maximum range of 500 meters

  Scenario: Animal hit detection
    Given I shoot in the direction of a deer
    When the projectile hits the deer collision sphere
    Then the deer should take damage based on weapon power
    And blood particles should appear at hit location
    And the deer should react immediately to being hit

  Scenario: Weapon reloading
    Given my rifle has 0 bullets remaining
    When I press 'R' key to reload
    Then the weapon should start 2-second reload animation
    And the ammo counter should show 'Reloading'
    And I should not be able to shoot during reload

  Scenario: Scope aiming and zoom
    Given I have a scoped rifle
    When I right-click to aim down sights
    Then the camera FOV should narrow for zoom effect
    And weapon sway should be reduced by 70%
    And I should be able to see distant targets clearly

  Scenario: Weapon accuracy and movement penalty
    Given I'm running and try to shoot
    Then the bullet spread should increase significantly
    And the chance to hit distant targets should decrease
    And the reticle should show weapon sway

  Scenario: Headshot bonus damage
    Given I hit an animal in the head area
    Then the damage should be multiplied by 1.5x
    And the animal should have immediate death chance
    And a visual indicator should show critical hit

  Scenario: Bullet drop compensation
    Given I'm shooting at a target 300 meters away
    When I aim at the target
    Then I should need to aim above the target to compensate for drop
    And the bullet should hit the target if properly aimed
    And missing should show bullet impact on terrain

  Scenario: Environmental effects on shooting
    Given it's raining heavily
    When I shoot at long distance
    Then bullet velocity should decrease by 10%
    And accuracy should be reduced due to wind gusts
    And I should see rain affecting bullet trajectory

  Scenario: Ammunition types and effects
    Given I have different caliber bullets
    When I select larger caliber
    Then the damage should increase
    And the bullet drop should be more pronounced
    And the recoil should be stronger

  Scenario: Ricochet and environmental hits
    Given I shoot at a rock
    When the bullet hits the surface
    Then the bullet should ricochet with reduced damage
    And a spark effect should appear
    And the bullet should continue in new direction
