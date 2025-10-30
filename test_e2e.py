"""
End-to-end test script for Visionary Lab API
Tests the complete workflow: generate → save → retrieve
"""

import requests
import json
import time
import sys
from typing import Dict, Optional

# Backend URL
BASE_URL = "https://ca-backend-sbuxstudio.delightfulground-306a1d02.eastus2.azurecontainerapps.io"
API_V1 = f"{BASE_URL}/api/v1"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")


def test_health_check() -> bool:
    """Test basic health check endpoint"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{API_V1}/health", timeout=10)
        if response.status_code == 200:
            print_success(f"Health check passed: {response.json()}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False


def test_env_status() -> bool:
    """Test environment variables status"""
    print_section("2. Environment Status")
    try:
        response = requests.get(f"{API_V1}/env/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_info(f"Set variables: {len(data.get('set', []))}")
            print_info(f"Missing variables: {len(data.get('missing', []))}")
            
            if data.get('missing'):
                print_error(f"Missing required variables: {', '.join(data['missing'])}")
                return False
            else:
                print_success("All required environment variables are set")
                return True
        else:
            print_error(f"Env status check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Env status check failed: {str(e)}")
        return False


def test_cosmos_health() -> bool:
    """Test Cosmos DB connectivity"""
    print_section("3. Cosmos DB Health")
    try:
        response = requests.get(f"{API_V1}/gallery/health", timeout=15)
        if response.status_code == 200:
            data = response.json()
            cosmos_status = data.get('cosmos_db', {})
            if cosmos_status.get('status') == 'healthy':
                print_success(f"Cosmos DB connection healthy")
                print_info(f"Database: {cosmos_status.get('database')}")
                print_info(f"Container: {cosmos_status.get('container')}")
                return True
            else:
                print_error(f"Cosmos DB unhealthy: {cosmos_status.get('error')}")
                return False
        else:
            print_error(f"Cosmos health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cosmos health check failed: {str(e)}")
        return False


def test_image_generation() -> Optional[Dict]:
    """Test image generation endpoint"""
    print_section("4. Image Generation")
    
    payload = {
        "prompt": "A serene coffee shop interior with warm lighting and wooden furniture",
        "model": "gpt-image-1",
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "png"
    }
    
    print_info(f"Generating image with prompt: '{payload['prompt'][:50]}...'")
    
    try:
        response = requests.post(
            f"{API_V1}/images/generate",
            json=payload,
            timeout=60  # Image generation can take time
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Debug: print the actual response structure
            print_info(f"Response keys: {list(data.keys())}")
            
            if data.get('success') and data.get('images'):
                image_count = len(data['images'])
                print_success(f"Generated {image_count} image(s)")
                
                # Print token usage if available
                if data.get('usage'):
                    usage = data['usage']
                    print_info(f"Tokens used: {usage.get('total_tokens', 'N/A')}")
                
                return data
            elif data.get('imgen_model_response'):
                # Handle the actual response structure
                print_info("Found imgen_model_response in response")
                model_resp = data.get('imgen_model_response', {})
                if isinstance(model_resp, dict) and model_resp.get('data'):
                    print_success(f"Generated {len(model_resp['data'])} image(s)")
                    # Reformat to expected structure
                    data['images'] = model_resp.get('data', [])
                    return data
                else:
                    print_error(f"Unexpected imgen_model_response structure: {type(model_resp)}")
                    print_info(f"Full response: {json.dumps(data, indent=2)[:500]}")
                    return None
            else:
                print_error(f"Generation succeeded but no images returned: {data.get('message')}")
                print_info(f"Full response: {json.dumps(data, indent=2)[:500]}")
                return None
        else:
            error_detail = response.text[:500]
            print_error(f"Image generation failed: {error_detail}")
            return None
            
    except requests.Timeout:
        print_error("Image generation timed out (60s)")
        return None
    except Exception as e:
        print_error(f"Image generation failed: {str(e)}")
        return None


def test_image_save(generation_data: Dict) -> Optional[str]:
    """Test saving generated image to storage and Cosmos DB"""
    print_section("5. Image Save")
    
    if not generation_data or not generation_data.get('images'):
        print_error("No generation data to save")
        return None
    
    image_data = generation_data['images'][0]
    
    save_payload = {
        "images": [image_data],
        "folder_path": "e2e-test",
        "metadata": {
            "test_type": "end_to_end",
            "test_timestamp": str(int(time.time())),
            "prompt": generation_data.get('prompt', '')
        }
    }
    
    print_info("Saving image to Azure Storage and Cosmos DB...")
    
    try:
        response = requests.post(
            f"{API_V1}/images/save",
            json=save_payload,
            timeout=30
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and data.get('saved_images'):
                saved = data['saved_images'][0]
                print_success(f"Image saved successfully")
                print_info(f"Asset ID: {saved.get('asset_id')}")
                print_info(f"Blob name: {saved.get('blob_name')}")
                print_info(f"URL: {saved.get('url')[:80]}...")
                
                return saved.get('asset_id')
            else:
                print_error(f"Save succeeded but no saved images: {data.get('message')}")
                return None
        else:
            error_detail = response.text[:500]
            print_error(f"Image save failed: {error_detail}")
            return None
            
    except Exception as e:
        print_error(f"Image save failed: {str(e)}")
        return None


def test_gallery_retrieval(asset_id: str) -> bool:
    """Test retrieving saved image from gallery"""
    print_section("6. Gallery Retrieval")
    
    print_info(f"Retrieving asset {asset_id} from gallery...")
    
    try:
        # Wait a moment for Cosmos DB consistency
        time.sleep(2)
        
        response = requests.get(
            f"{API_V1}/gallery/images",
            params={"limit": 50, "offset": 0},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print_info(f"Found {len(items)} total images in gallery")
            
            # Look for our asset
            found = False
            for item in items:
                if item.get('id') == asset_id:
                    found = True
                    print_success(f"Found saved image in gallery")
                    print_info(f"Name: {item.get('name')}")
                    print_info(f"Size: {item.get('size')} bytes")
                    print_info(f"Folder: {item.get('folder_path', 'root')}")
                    break
            
            if not found:
                print_error(f"Asset {asset_id} not found in gallery")
                print_info("This might be a timing issue - checking metadata directly...")
                return test_metadata_retrieval(asset_id)
            
            return found
        else:
            print_error(f"Gallery retrieval failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Gallery retrieval failed: {str(e)}")
        return False


def test_metadata_retrieval(asset_id: str) -> bool:
    """Test retrieving metadata directly from Cosmos DB"""
    print_info("Checking metadata directly...")
    
    try:
        response = requests.get(
            f"{API_V1}/metadata/{asset_id}",
            params={"media_type": "image"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('metadata'):
                print_success("Metadata found in Cosmos DB")
                metadata = data['metadata']
                print_info(f"Blob: {metadata.get('blob_name')}")
                print_info(f"Container: {metadata.get('container')}")
                return True
            else:
                print_error("Metadata not found")
                return False
        else:
            print_error(f"Metadata retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Metadata retrieval failed: {str(e)}")
        return False


def test_pipeline_endpoint() -> bool:
    """Test the complete pipeline endpoint (generate + save in one call)"""
    print_section("7. Pipeline Endpoint (Generate + Save)")
    
    pipeline_payload = {
        "actions": ["generate", "save"],
        "prompt": "A modern tech workspace with multiple monitors",
        "model": "gpt-image-1",
        "n": 1,
        "size": "1024x1024",
        "quality": "high",
        "output_format": "png",
        "save_options": {
            "folder_path": "e2e-test-pipeline",
            "metadata": {
                "test_type": "pipeline",
                "test_timestamp": str(int(time.time()))
            }
        }
    }
    
    print_info("Running pipeline: generate + save...")
    
    try:
        response = requests.post(
            f"{API_V1}/images/pipeline",
            json=pipeline_payload,
            timeout=90  # Pipeline can take longer
        )
        
        print_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print_success("Pipeline completed successfully")
                
                # Check individual steps
                steps = data.get('steps', [])
                for step in steps:
                    action = step.get('action')
                    success = step.get('success')
                    status = Colors.GREEN + "✓" if success else Colors.RED + "✗"
                    print(f"  {status} {action}: {step.get('message', 'OK')}{Colors.RESET}")
                
                # Print final results
                if data.get('final_images'):
                    print_info(f"Final images: {len(data['final_images'])}")
                    
                return True
            else:
                print_error(f"Pipeline failed: {data.get('message')}")
                return False
        else:
            error_detail = response.text[:500]
            print_error(f"Pipeline failed: {error_detail}")
            return False
            
    except requests.Timeout:
        print_error("Pipeline timed out (90s)")
        return False
    except Exception as e:
        print_error(f"Pipeline failed: {str(e)}")
        return False


def main():
    """Run all end-to-end tests"""
    print(f"\n{Colors.BOLD}Visionary Lab - End-to-End API Tests{Colors.RESET}")
    print(f"Backend: {BASE_URL}\n")
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = test_health_check()
    if not results['health']:
        print_error("\nBackend is not responding. Stopping tests.")
        sys.exit(1)
    
    # Test 2: Environment Status
    results['env'] = test_env_status()
    if not results['env']:
        print_error("\nEnvironment variables not configured. Some tests may fail.")
    
    # Test 3: Cosmos DB Health
    results['cosmos'] = test_cosmos_health()
    
    # Test 4: Image Generation
    generation_data = test_image_generation()
    results['generation'] = generation_data is not None
    
    if generation_data:
        # Test 5: Image Save
        asset_id = test_image_save(generation_data)
        results['save'] = asset_id is not None
        
        if asset_id:
            # Test 6: Gallery Retrieval
            results['gallery'] = test_gallery_retrieval(asset_id)
    else:
        results['save'] = False
        results['gallery'] = False
    
    # Test 7: Pipeline Endpoint
    results['pipeline'] = test_pipeline_endpoint()
    
    # Summary
    print_section("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASS" if passed else f"{Colors.RED}FAIL"
        print(f"{status}{Colors.RESET} - {test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed_tests}/{total_tests} tests passed{Colors.RESET}")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}All tests passed! ✓{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}Some tests failed ✗{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
