"""
D-LEVEL CUSTOM PROJECT - Enemy Profiles

Defines per-enemy-type tuning parameters.
This replaces subclass-based behaviour differences.
"""

ENEMY_PROFILES = {
    "BROWN": {
        "max_speed": 0.0,
        "max_projectiles": 1,
        "fire_rate": 3.0,
    },

    "GREY": {
        "max_speed": 40.0,
        "max_projectiles": 1,
        "fire_rate": 2.5,
    },

    "TEAL": {
        "max_speed": 60.0,
        "max_projectiles": 2,
        "fire_rate": 2.0,
    },

    "YELLOW": {
        "max_speed": 70.0,
        "max_projectiles": 2,
        "fire_rate": 1.8,
    },

    "RED": {
        "max_speed": 80.0,
        "max_projectiles": 3,
        "fire_rate": 1.5,
    },

    "GREEN": {
        "max_speed": 90.0,
        "max_projectiles": 3,
        "fire_rate": 1.4,
    },

    "PURPLE": {
        "max_speed": 100.0,
        "max_projectiles": 3,
        "fire_rate": 1.2,
    },

    "WHITE": {
        "max_speed": 110.0,
        "max_projectiles": 4,
        "fire_rate": 1.0,
    },

    "BLACK": {
        "max_speed": 120.0,
        "max_projectiles": 4,
        "fire_rate": 0.9,
    },
}