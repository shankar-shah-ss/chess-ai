# config_validator.py - Comprehensive configuration validation system
import json
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from error_handling import safe_execute, logger

class ConfigValidator:
    """Comprehensive configuration validation and management"""
    
    def __init__(self):
        self.validation_rules = self._setup_validation_rules()
        self.default_config = self._get_default_config()
        self.validation_errors = []
    
    def _setup_validation_rules(self) -> Dict[str, Dict]:
        """Setup validation rules for all configuration sections"""
        return {
            'engine': {
                'stockfish_path': {
                    'type': str,
                    'required': True,
                    'validator': self._validate_executable_path
                },
                'default_depth': {
                    'type': int,
                    'required': True,
                    'min': 1,
                    'max': 30,
                    'default': 15
                },
                'default_skill_level': {
                    'type': int,
                    'required': True,
                    'min': 0,
                    'max': 20,
                    'default': 10
                },
                'max_depth': {
                    'type': int,
                    'required': True,
                    'min': 1,
                    'max': 50,
                    'default': 20
                },
                'max_skill_level': {
                    'type': int,
                    'required': True,
                    'min': 0,
                    'max': 20,
                    'default': 20
                },
                'timeout_seconds': {
                    'type': int,
                    'required': True,
                    'min': 1,
                    'max': 300,
                    'default': 30
                },
                'threads': {
                    'type': int,
                    'required': False,
                    'min': 1,
                    'max': 16,
                    'default': 2
                },
                'hash_size_mb': {
                    'type': int,
                    'required': False,
                    'min': 16,
                    'max': 2048,
                    'default': 128
                }
            },
            'ui': {
                'window_width': {
                    'type': int,
                    'required': True,
                    'min': 800,
                    'max': 3840,
                    'default': 1200
                },
                'window_height': {
                    'type': int,
                    'required': True,
                    'min': 600,
                    'max': 2160,
                    'default': 800
                },
                'fullscreen': {
                    'type': bool,
                    'required': True,
                    'default': False
                },
                'theme_index': {
                    'type': int,
                    'required': True,
                    'min': 0,
                    'max': 10,
                    'default': 1
                },
                'show_coordinates': {
                    'type': bool,
                    'required': True,
                    'default': True
                },
                'show_move_history': {
                    'type': bool,
                    'required': True,
                    'default': True
                },
                'show_evaluation_bar': {
                    'type': bool,
                    'required': True,
                    'default': True
                },
                'animation_speed': {
                    'type': float,
                    'required': True,
                    'min': 0.1,
                    'max': 3.0,
                    'default': 1.0
                },
                'font_size': {
                    'type': int,
                    'required': False,
                    'min': 8,
                    'max': 72,
                    'default': 14
                },
                'font_family': {
                    'type': str,
                    'required': False,
                    'default': 'Arial'
                }
            },
            'analysis': {
                'auto_analyze': {
                    'type': bool,
                    'required': True,
                    'default': False
                },
                'analysis_depth': {
                    'type': int,
                    'required': True,
                    'min': 10,
                    'max': 30,
                    'default': 18
                },
                'max_analysis_time': {
                    'type': int,
                    'required': True,
                    'min': 60,
                    'max': 1800,
                    'default': 300
                },
                'show_best_moves': {
                    'type': int,
                    'required': True,
                    'min': 1,
                    'max': 5,
                    'default': 3
                },
                'classification_thresholds': {
                    'type': dict,
                    'required': True,
                    'validator': self._validate_classification_thresholds,
                    'default': {
                        'BLUNDER': 3.0,
                        'MISTAKE': 1.5,
                        'INACCURACY': 0.5,
                        'OKAY': 0.25
                    }
                },
                'enable_opening_book': {
                    'type': bool,
                    'required': False,
                    'default': True
                },
                'cache_analysis': {
                    'type': bool,
                    'required': False,
                    'default': True
                }
            },
            'game': {
                'default_game_mode': {
                    'type': int,
                    'required': True,
                    'min': 0,
                    'max': 2,
                    'default': 0
                },
                'auto_save_pgn': {
                    'type': bool,
                    'required': True,
                    'default': True
                },
                'pgn_directory': {
                    'type': str,
                    'required': True,
                    'validator': self._validate_directory_path,
                    'default': 'games'
                },
                'sound_enabled': {
                    'type': bool,
                    'required': True,
                    'default': True
                },
                'move_validation': {
                    'type': bool,
                    'required': True,
                    'default': True
                },
                'auto_promote_queen': {
                    'type': bool,
                    'required': False,
                    'default': False
                },
                'highlight_legal_moves': {
                    'type': bool,
                    'required': False,
                    'default': True
                }
            },
            'performance': {
                'max_memory_mb': {
                    'type': int,
                    'required': False,
                    'min': 256,
                    'max': 8192,
                    'default': 1024
                },
                'max_threads': {
                    'type': int,
                    'required': False,
                    'min': 2,
                    'max': 32,
                    'default': 8
                },
                'cache_cleanup_interval': {
                    'type': int,
                    'required': False,
                    'min': 30,
                    'max': 3600,
                    'default': 300
                },
                'enable_performance_monitoring': {
                    'type': bool,
                    'required': False,
                    'default': True
                }
            }
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Generate default configuration from validation rules"""
        default_config = {}
        
        for section, rules in self.validation_rules.items():
            default_config[section] = {}
            for key, rule in rules.items():
                if 'default' in rule:
                    default_config[section][key] = rule['default']
        
        return default_config
    
    @safe_execute(fallback_value=True, context="config_validation")
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate entire configuration"""
        self.validation_errors.clear()
        is_valid = True
        
        # Check all required sections exist
        for section_name in self.validation_rules.keys():
            if section_name not in config:
                self.validation_errors.append(f"Missing required section: {section_name}")
                is_valid = False
                continue
            
            # Validate section
            if not self._validate_section(section_name, config[section_name]):
                is_valid = False
        
        # Log validation results
        if is_valid:
            logger.info("Configuration validation passed")
        else:
            logger.error(f"Configuration validation failed: {self.validation_errors}")
        
        return is_valid
    
    def _validate_section(self, section_name: str, section_config: Dict[str, Any]) -> bool:
        """Validate a configuration section"""
        if section_name not in self.validation_rules:
            self.validation_errors.append(f"Unknown section: {section_name}")
            return False
        
        rules = self.validation_rules[section_name]
        is_valid = True
        
        # Check required fields
        for key, rule in rules.items():
            if rule.get('required', False) and key not in section_config:
                self.validation_errors.append(f"Missing required field: {section_name}.{key}")
                is_valid = False
                continue
            
            if key in section_config:
                if not self._validate_field(section_name, key, section_config[key], rule):
                    is_valid = False
        
        return is_valid
    
    def _validate_field(self, section: str, key: str, value: Any, rule: Dict[str, Any]) -> bool:
        """Validate a single configuration field"""
        field_path = f"{section}.{key}"
        
        # Type validation
        expected_type = rule.get('type')
        if expected_type and not isinstance(value, expected_type):
            self.validation_errors.append(f"Invalid type for {field_path}: expected {expected_type.__name__}, got {type(value).__name__}")
            return False
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            if 'min' in rule and value < rule['min']:
                self.validation_errors.append(f"Value too small for {field_path}: {value} < {rule['min']}")
                return False
            
            if 'max' in rule and value > rule['max']:
                self.validation_errors.append(f"Value too large for {field_path}: {value} > {rule['max']}")
                return False
        
        # Custom validator
        if 'validator' in rule:
            try:
                if not rule['validator'](value):
                    self.validation_errors.append(f"Custom validation failed for {field_path}")
                    return False
            except Exception as e:
                self.validation_errors.append(f"Validator error for {field_path}: {e}")
                return False
        
        return True
    
    def _validate_executable_path(self, path: str) -> bool:
        """Validate executable path"""
        if not path:
            return False
        
        # Check if it's just a command name (will be found in PATH)
        if '/' not in path and '\\' not in path:
            return True
        
        # Check if file exists and is executable
        path_obj = Path(path)
        return path_obj.exists() and os.access(path, os.X_OK)
    
    def _validate_directory_path(self, path: str) -> bool:
        """Validate directory path (create if doesn't exist)"""
        if not path:
            return False
        
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    def _validate_classification_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """Validate move classification thresholds"""
        required_keys = {'BLUNDER', 'MISTAKE', 'INACCURACY', 'OKAY'}
        
        if not isinstance(thresholds, dict):
            return False
        
        # Check required keys
        if not required_keys.issubset(thresholds.keys()):
            return False
        
        # Check values are positive numbers in descending order
        values = [thresholds[key] for key in ['BLUNDER', 'MISTAKE', 'INACCURACY', 'OKAY']]
        
        for value in values:
            if not isinstance(value, (int, float)) or value < 0:
                return False
        
        # Should be in descending order
        return values == sorted(values, reverse=True)
    
    def fix_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fix configuration by applying defaults and corrections"""
        fixed_config = config.copy()
        
        # Add missing sections
        for section_name in self.validation_rules.keys():
            if section_name not in fixed_config:
                fixed_config[section_name] = {}
        
        # Fix each section
        for section_name, rules in self.validation_rules.items():
            section_config = fixed_config[section_name]
            
            for key, rule in rules.items():
                # Add missing required fields with defaults
                if key not in section_config and 'default' in rule:
                    section_config[key] = rule['default']
                    logger.info(f"Added default value for {section_name}.{key}: {rule['default']}")
                
                # Fix invalid values
                if key in section_config:
                    fixed_value = self._fix_field_value(section_config[key], rule)
                    if fixed_value != section_config[key]:
                        logger.info(f"Fixed value for {section_name}.{key}: {section_config[key]} -> {fixed_value}")
                        section_config[key] = fixed_value
        
        return fixed_config
    
    def _fix_field_value(self, value: Any, rule: Dict[str, Any]) -> Any:
        """Fix a single field value"""
        # Type conversion
        expected_type = rule.get('type')
        if expected_type and not isinstance(value, expected_type):
            try:
                if expected_type == bool:
                    return bool(value) if isinstance(value, (int, str)) else rule.get('default', False)
                elif expected_type == int:
                    return int(float(value)) if isinstance(value, (str, float)) else rule.get('default', 0)
                elif expected_type == float:
                    return float(value) if isinstance(value, (str, int)) else rule.get('default', 0.0)
                elif expected_type == str:
                    return str(value)
            except (ValueError, TypeError):
                return rule.get('default', value)
        
        # Range fixing for numbers
        if isinstance(value, (int, float)):
            if 'min' in rule and value < rule['min']:
                return rule['min']
            if 'max' in rule and value > rule['max']:
                return rule['max']
        
        return value
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self.validation_errors.copy()
    
    def create_config_template(self, filepath: str = "config_template.json"):
        """Create a configuration template file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.default_config, f, indent=2)
            logger.info(f"Configuration template created: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to create config template: {e}")
            return False
    
    def validate_and_fix_file(self, filepath: str) -> bool:
        """Validate and fix configuration file"""
        try:
            # Load config
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            # Validate
            if self.validate_config(config):
                logger.info(f"Configuration file {filepath} is valid")
                return True
            
            # Fix and save
            fixed_config = self.fix_config(config)
            
            # Backup original
            backup_path = f"{filepath}.backup"
            os.rename(filepath, backup_path)
            logger.info(f"Original config backed up to {backup_path}")
            
            # Save fixed config
            with open(filepath, 'w') as f:
                json.dump(fixed_config, f, indent=2)
            
            logger.info(f"Configuration file {filepath} has been fixed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate/fix config file {filepath}: {e}")
            return False

# Global config validator instance
config_validator = ConfigValidator()