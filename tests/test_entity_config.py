"""Unit tests for entity type configuration."""

import tempfile
from pathlib import Path

import yaml

from scruby.config import load_config
from scruby.redactor import Redactor


class TestEntityConfiguration:
    """Test configurable entity type detection and redaction."""
    
    def test_exclude_organization_entity(self):
        """Test that ORGANIZATION can be excluded from redaction."""
        # Create config excluding ORGANIZATION
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": [
                "PERSON",
                "EMAIL_ADDRESS"
            ]
        }
        
        # Create redactor with config
        redactor = Redactor(config=config_data)
        
        # Test text with person, org, and email
        text = "John Smith works at Acme Corporation and his email is john@acme.com"
        result = redactor.redact({"content": text, "metadata": {}})
        
        # PERSON should be redacted
        assert "John Smith" not in result["content"], "PERSON should be redacted"
        
        # EMAIL should be redacted  
        assert "john@acme.com" not in result["content"], "EMAIL should be redacted"
        
        # ORGANIZATION should NOT be redacted (not in config)
        assert "Acme Corporation" in result["content"], "ORGANIZATION should not be redacted"
        
        print("✅ ORGANIZATION exclusion test passed")
    
    def test_include_only_specific_entities(self):
        """Test including only specific entity types."""
        # Config with only EMAIL_ADDRESS
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": ["EMAIL_ADDRESS"]
        }
        
        redactor = Redactor(config=config_data)
        
        text = "Contact John Smith at john@example.com or call 555-1234"
        result = redactor.redact({"content": text, "metadata": {}})
        
        # Only EMAIL should be redacted
        assert "john@example.com" not in result["content"], "EMAIL should be redacted"
        assert "John Smith" in result["content"], "PERSON should not be redacted"
        assert "555-1234" in result["content"], "PHONE should not be redacted"
        
        print("✅ Specific entity inclusion test passed")
    
    def test_multiple_entity_exclusions(self):
        """Test excluding multiple entity types."""
        # Include PERSON and EMAIL, but not PHONE or ORGANIZATION
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": [
                "PERSON",
                "EMAIL_ADDRESS"
            ]
        }
        
        redactor = Redactor(config=config_data)
        
        text = "John Smith (john@example.com) at Acme Corp, phone: 555-1234"
        result = redactor.redact({"content": text, "metadata": {}})
        
        # Included entities should be redacted
        assert "John Smith" not in result["content"]
        assert "john@example.com" not in result["content"]
        
        # Excluded entities should remain
        assert "Acme Corp" in result["content"]
        assert "555-1234" in result["content"]
        
        print("✅ Multiple exclusions test passed")
    
    def test_config_from_yaml_file(self):
        """Test loading entity config from YAML file."""
        # Create temp YAML config
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": [
                "PERSON",
                "US_SSN"
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Load config from file
            config = load_config(config_path)
            redactor = Redactor(config=config)
            
            text = "John Smith, SSN: 123-45-6789, email: john@example.com"
            result = redactor.redact({"content": text, "metadata": {}})
            
            # Configured entities should be redacted
            assert "John Smith" not in result["content"]
            assert "123-45-6789" not in result["content"]
            
            # Non-configured entities should remain
            assert "john@example.com" in result["content"]
            
            print("✅ YAML config file test passed")
        finally:
            Path(config_path).unlink()
    
    def test_comprehensive_entity_list(self):
        """Test with comprehensive entity list."""
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": [
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "US_SSN",
                "CREDIT_CARD",
                "URL",
                "LOCATION"
                # Notably excludes ORGANIZATION and DATE_TIME
            ]
        }
        
        redactor = Redactor(config=config_data)
        
        text = "Jane Doe (jane@test.com) at Tech Inc, located in New York, SSN: 111-22-3333"
        result = redactor.redact({"content": text, "metadata": {}})
        
        # Included entities should be redacted
        assert "Jane Doe" not in result["content"]
        assert "jane@test.com" not in result["content"]
        assert "New York" not in result["content"]
        assert "111-22-3333" not in result["content"]
        
        # Excluded ORGANIZATION should remain
        assert "Tech Inc" in result["content"]
        
        print("✅ Comprehensive entity list test passed")
    
    def test_default_entity_list(self):
        """Test with empty/default entity list (uses all default entities)."""
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": []
        }
        
        redactor = Redactor(config=config_data)
        
        text = "John Smith at john@example.com, SSN: 123-45-6789"
        result = redactor.redact({"content": text, "metadata": {}})
        
        # With empty list, Presidio uses all default recognizers
        # Should detect multiple entities (PERSON, EMAIL, SSN, etc.)
        assert result["metadata"]["redacted_entities"] > 0, \
            "Should detect default entities with empty list"
        
        # At least some common entities should be redacted
        assert "john@example.com" not in result["content"], "EMAIL should be redacted by default"
        
        print("✅ Default entity list test passed")
    
    def test_entity_count_matches_config(self):
        """Test that entity count reflects configured entities only."""
        # Config with only 2 entity types
        config_data = {
            "hmac_secret": "test-key",
            "entities_to_redact": ["PERSON", "EMAIL_ADDRESS"]
        }
        
        redactor = Redactor(config=config_data)
        
        # Text with multiple entity types
        text = "Contact John Smith (john@example.com) at Acme Corp, phone: 555-1234, SSN: 123-45-6789"
        result = redactor.redact({"content": text, "metadata": {}})
        
        # Should only count the 2 configured entity types
        entity_count = result["metadata"]["redacted_entities"]
        assert entity_count == 2, f"Should detect 2 entities (PERSON + EMAIL), found {entity_count}"
        
        print("✅ Entity count test passed")


if __name__ == "__main__":
    # Run all tests
    test = TestEntityConfiguration()
    
    print("=" * 60)
    print("Testing Entity Type Configuration")
    print("=" * 60)
    
    test.test_exclude_organization_entity()
    test.test_include_only_specific_entities()
    test.test_multiple_entity_exclusions()
    test.test_config_from_yaml_file()
    test.test_comprehensive_entity_list()
    test.test_default_entity_list()
    test.test_entity_count_matches_config()
    
    print("\n" + "=" * 60)
    print("✅ ALL ENTITY CONFIGURATION TESTS PASSED!")
    print("=" * 60)
