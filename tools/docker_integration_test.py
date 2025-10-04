"""
Docker Integration Test for Sebastián's Components
Tests the complete Docker environment with Alejandro's components
"""

import os
import sys
import time
import zmq
import json
import subprocess
import threading
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message
from common.time_utils import now_ms


class DockerIntegrationTest:
    """Comprehensive Docker integration test"""
    
    def __init__(self):
        self.results = []
        self.processes = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": now_ms()
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def check_docker_running(self) -> bool:
        """Check if Docker is running"""
        try:
            result = subprocess.run(['docker', 'info'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def build_docker_image(self) -> bool:
        """Build Docker image"""
        try:
            print("🔨 Building Docker image...")
            result = subprocess.run(['docker-compose', 'build'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                self.log_test("Docker Build", True, "Image built successfully")
                return True
            else:
                self.log_test("Docker Build", False, f"Build failed: {result.stderr}")
                return False
        except Exception as e:
            self.log_test("Docker Build", False, f"Build error: {str(e)}")
            return False
    
    def start_containers(self) -> bool:
        """Start Docker containers"""
        try:
            print("🚀 Starting Docker containers...")
            result = subprocess.run(['docker-compose', 'up', '-d'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.log_test("Docker Start", True, "Containers started successfully")
                return True
            else:
                self.log_test("Docker Start", False, f"Start failed: {result.stderr}")
                return False
        except Exception as e:
            self.log_test("Docker Start", False, f"Start error: {str(e)}")
            return False
    
    def wait_for_services(self) -> bool:
        """Wait for services to be ready"""
        services = [
            (5555, "GC Server"),
            (5556, "GC PUB"),
            (5557, "AP Actor"),
            (5560, "GA Server"),
            (5564, "GA Health"),
            (5565, "GA Heartbeat")
        ]
        
        all_ready = True
        for port, name in services:
            if not self.wait_for_port(port, timeout=30):
                self.log_test(f"Service {name}", False, f"Port {port} not ready")
                all_ready = False
            else:
                self.log_test(f"Service {name}", True, f"Port {port} ready")
        
        return all_ready
    
    def wait_for_port(self, port: int, timeout: int = 10) -> bool:
        """Wait for a port to be available"""
        import socket
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.5)
        return False
    
    def test_gc_connection(self) -> bool:
        """Test connection to GC"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test PRESTAR request
            request = {
                'id': f'docker-test-{now_ms()}',
                'sedeId': 'A',
                'userId': 'u-docker-test',
                'op': 'PRESTAR',
                'libroCodigo': 'ISBN-0001',
                'timestamp': now_ms()
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('status') in ['OK', 'ERROR']:
                self.log_test("GC Connection", True, f"Response: {response.get('status')}")
                return True
            else:
                self.log_test("GC Connection", False, f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            self.log_test("GC Connection", False, str(e))
            return False
        finally:
            socket.close()
            context.term()
    
    def test_ap_connection(self) -> bool:
        """Test connection to AP actor"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5557')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test loan request
            request = {
                'id': f'docker-ap-test-{now_ms()}',
                'libroCodigo': 'ISBN-0002',
                'userId': 'u-docker-ap-test'
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('ok') is not None:
                self.log_test("AP Connection", True, f"Response: {response}")
                return True
            else:
                self.log_test("AP Connection", False, f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            self.log_test("AP Connection", False, str(e))
            return False
        finally:
            socket.close()
            context.term()
    
    def test_ga_connection(self) -> bool:
        """Test connection to GA server"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5560')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test loan request
            request = {
                'method': 'checkAndLoan',
                'payload': {
                    'id': f'docker-ga-test-{now_ms()}',
                    'libroCodigo': 'ISBN-0003',
                    'userId': 'u-docker-ga-test'
                }
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('ok') is not None:
                self.log_test("GA Connection", True, f"Response: {response}")
                return True
            else:
                self.log_test("GA Connection", False, f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            self.log_test("GA Connection", False, str(e))
            return False
        finally:
            socket.close()
            context.term()
    
    def test_ga_health(self) -> bool:
        """Test GA health endpoint"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5564')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test health check
            request = {'status': 'check'}
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('status') == 'ok':
                self.log_test("GA Health", True, f"Health check passed: {response}")
                return True
            else:
                self.log_test("GA Health", False, f"Health check failed: {response}")
                return False
                
        except Exception as e:
            self.log_test("GA Health", False, str(e))
            return False
        finally:
            socket.close()
            context.term()
    
    def test_load_generator(self) -> bool:
        """Test load generator"""
        try:
            print("🔄 Running load generator test...")
            result = subprocess.run([
                'docker-compose', 'run', '--rm', 'load-generator'
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                self.log_test("Load Generator", True, "Load test completed successfully")
                return True
            else:
                self.log_test("Load Generator", False, f"Load test failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_test("Load Generator", False, f"Load test error: {str(e)}")
            return False
    
    def stop_containers(self):
        """Stop Docker containers"""
        try:
            print("🛑 Stopping Docker containers...")
            result = subprocess.run(['docker-compose', 'down'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Containers stopped successfully")
            else:
                print(f"⚠️ Error stopping containers: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Error stopping containers: {str(e)}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Docker integration tests"""
        print("🐳 Starting Docker Integration Tests")
        print("=" * 60)
        
        # Check Docker
        if not self.check_docker_running():
            self.log_test("Docker Check", False, "Docker is not running")
            return {
                'total_tests': 1,
                'passed_tests': 0,
                'failed_tests': 1,
                'success_rate': 0,
                'results': self.results
            }
        
        self.log_test("Docker Check", True, "Docker is running")
        
        try:
            # Build image
            if not self.build_docker_image():
                return self._get_results()
            
            # Start containers
            if not self.start_containers():
                return self._get_results()
            
            # Wait for services
            if not self.wait_for_services():
                return self._get_results()
            
            # Test connections
            print("\n🔗 Testing service connections...")
            self.test_gc_connection()
            self.test_ap_connection()
            self.test_ga_connection()
            self.test_ga_health()
            
            # Test load generator
            print("\n📊 Testing load generator...")
            self.test_load_generator()
            
        finally:
            # Always cleanup
            self.stop_containers()
        
        return self._get_results()
    
    def _get_results(self) -> Dict[str, Any]:
        """Get test results summary"""
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print("\n📊 Docker Integration Test Summary:")
        print("=" * 60)
        
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': passed / total if total > 0 else 0,
            'results': self.results
        }


def main():
    """Main function to run Docker integration tests"""
    test = DockerIntegrationTest()
    results = test.run_all_tests()
    
    if results['success_rate'] >= 0.8:
        print("\n🎉 Docker integration tests mostly successful!")
        return 0
    else:
        print("\n💥 Docker integration tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
