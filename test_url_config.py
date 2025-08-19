#!/usr/bin/env python3
"""
Test script for URL configuration system.

This script tests all the URL configuration functions to ensure they work correctly.
"""

import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.urls import (
    get_site_vacancy_url,
    get_site_company_url,
    get_site_api_url,
    get_site_logo_url,
    get_placeholder_image,
    reload_url_config
)


def test_url_functions():
    """Test all URL configuration functions."""
    print("🧪 Testing URL Configuration System")
    print("=" * 50)
    
    # Test placeholder images
    print("\n📸 Testing Placeholder Images:")
    try:
        job_img = get_placeholder_image("job_opportunity")
        company_img = get_placeholder_image("company")
        geekjob_img = get_placeholder_image("geekjob")
        hh_img = get_placeholder_image("headhunter")
        
        print(f"✅ Job opportunity: {job_img}")
        print(f"✅ Company: {company_img}")
        print(f"✅ GeekJob: {geekjob_img}")
        print(f"✅ HeadHunter: {hh_img}")
    except Exception as e:
        print(f"❌ Placeholder images failed: {e}")
    
    # Test HeadHunter URLs
    print("\n🔍 Testing HeadHunter URLs:")
    try:
        hh_vacancy = get_site_vacancy_url('hh', '12345')
        hh_company = get_site_company_url('hh', 'employer123')
        hh_api = get_site_api_url('hh')
        hh_logo = get_site_logo_url('hh', 'employer123', size='240')
        
        print(f"✅ Vacancy: {hh_vacancy}")
        print(f"✅ Company: {hh_company}")
        print(f"✅ API: {hh_api}")
        print(f"✅ Logo: {hh_logo}")
    except Exception as e:
        print(f"❌ HeadHunter URLs failed: {e}")
    
    # Test GeekJob URLs
    print("\n🔍 Testing GeekJob URLs:")
    try:
        gj_vacancy = get_site_vacancy_url('geekjob', '67890')
        gj_company = get_site_company_url('geekjob', 'company456')
        gj_api = get_site_api_url('geekjob')
        gj_logo = get_site_logo_url('geekjob', None, 'logo.png')
        
        print(f"✅ Vacancy: {gj_vacancy}")
        print(f"✅ Company: {gj_company}")
        print(f"✅ API: {gj_api}")
        print(f"✅ Logo: {gj_logo}")
    except Exception as e:
        print(f"❌ GeekJob URLs failed: {e}")
    
    # Test fallback URLs
    print("\n🔄 Testing Fallback URLs:")
    try:
        # Test with non-existent site
        fallback_vacancy = get_site_vacancy_url('nonexistent', '99999')
        fallback_company = get_site_company_url('nonexistent', 'company999')
        
        print(f"✅ Fallback vacancy: {fallback_vacancy}")
        print(f"✅ Fallback company: {fallback_company}")
    except Exception as e:
        print(f"❌ Fallback URLs failed: {e}")
    
    # Test configuration reloading
    print("\n🔄 Testing Configuration Reloading:")
    try:
        reload_url_config()
        print("✅ Configuration reloaded successfully")
    except Exception as e:
        print(f"❌ Configuration reload failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 URL Configuration Test Complete!")


def test_url_validation():
    """Test URL validation functions."""
    print("\n🔍 Testing URL Validation:")
    
    from config.urls import URLConfig
    
    url_config = URLConfig()
    
    # Test valid URLs from configuration
    try:
        # Load URLs from configuration
        with open('config/urls.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Get URLs from configuration
        hh_api = config.get('job_sites', {}).get('hh', {}).get('urls', {}).get('api', 'https://api.hh.ru/vacancies')
        gj_api = config.get('job_sites', {}).get('geekjob', {}).get('urls', {}).get('api', 'https://geekjob.ru/json/find/vacancy')
        placeholder = config.get('external_services', {}).get('placeholder_images', {}).get('job_opportunity', 'https://img.icons8.com/color/96/000000/job.png')
        
        valid_urls = [
            hh_api,
            gj_api,
            placeholder
        ]
        
        for url in valid_urls:
            is_valid = url_config.validate_url(url)
            status = "✅" if is_valid else "❌"
            print(f"{status} {url}: {is_valid}")
            
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to hardcoded URLs if configuration cannot be loaded
        valid_urls = [
            "https://api.hh.ru/vacancies",
            "https://geekjob.ru/json/find/vacancy",
            "https://img.icons8.com/color/96/000000/job.png"
        ]
        
        for url in valid_urls:
            is_valid = url_config.validate_url(url)
            status = "✅" if is_valid else "❌"
            print(f"{status} {url}: {is_valid}")
    
    # Test invalid URLs
    invalid_urls = [
        "",
        "not-a-url",
        "ftp://example.com",
        None
    ]
    
    for url in invalid_urls:
        is_valid = url_config.validate_url(url)
        status = "✅" if not is_valid else "❌"
        print(f"{status} {url}: {not is_valid}")


if __name__ == "__main__":
    try:
        test_url_functions()
        test_url_validation()
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 