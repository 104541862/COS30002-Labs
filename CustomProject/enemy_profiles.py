"""
D-LEVEL CUSTOM PROJECT - Enemy Profiles

Defines per-enemy-type tuning parameters.
This replaces subclass-based behaviour differences.
"""

ENEMY_PROFILES = {
    "BROWN": {
        "max_speed": 0.0,
        "max_projectiles": 1,
        "fire_rate": 0.5,
        "bullet_speed": 120,
    },

    "GREY": {
        "max_speed": 40.0,
        "max_projectiles": 1,
        "fire_rate": 0.5,
        "bullet_speed": 120
    },

    "TEAL": {
        "max_speed": 40.0,
        "max_projectiles": 2,
        "fire_rate": 10.0,
        "bullet_speed": 300
    },

    "YELLOW": {
        "max_speed": 70.0,
        "max_projectiles": 2,
        "fire_rate": 0.5,
        "bullet_speed": 200
    },

    "RED": {
        "max_speed": 100.0,
        "max_projectiles": 3,
        "fire_rate": 0.5,
        "bullet_speed": 200
    },

    "GREEN": {
        "max_speed": 0.0,
        "max_projectiles": 1,
        "fire_rate": 0.5,
        "bullet_speed": 400
    },

    "PURPLE": {
        "max_speed": 100.0,
        "max_projectiles": 5,
        "fire_rate": 0.5,
        "bullet_speed": 200
    },

    "WHITE": {
        "max_speed": 110.0,
        "max_projectiles": 4,
        "fire_rate": 0.5,
        "bullet_speed": 200
    },

    "BLACK": {
        "max_speed": 120.0,
        "max_projectiles": 2,
        "fire_rate": 0.5,
        "bullet_speed": 300
    },
}