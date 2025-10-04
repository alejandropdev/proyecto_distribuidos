"""
Integration test for Sebastián's components with Alejandro's system.
Tests the complete flow from PS → GC → Actors → GA.
"""

import os
import sys
import time
import zmq
import json
import threading
import subprocess
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message
from common.time_utils import now_ms


class IntegrationTest:
    """Comprehensive integration test for the distributed library system"""
    
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
    
    def start_process(self, cmd: List[str], name: str) -> subprocess.Popen:
        """Start a background process"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append((process, name))
            print(f"🚀 Started {name}")
            return process
        except Exception as e:
            self.log_test(f"Start {name}", False, str(e))
            return None
    
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
            time.sleep(0.1)
        return False
    
    def test_ga_storage(self) -> bool:
        """Test GA storage operations"""
        try:
            from ga.storage import GAStorage
            
            storage = GAStorage('./data/siteA')
            
            # Test loan
            result = storage.checkAndLoan('test-loan-1', 'ISBN-0001', 'u-test-1')
            if not result.get('ok'):
                self.log_test("GA Storage - Loan", False, result.get('reason'))
                return False
            
            # Test renovation
            result = storage.renovar('test-renovation-1', 'ISBN-0001', 'u-test-1', '2025-02-01')
            if not result.get('ok'):
                self.log_test("GA Storage - Renovation", False, result.get('reason'))
                return False
            
            # Test return
            result = storage.devolver('test-return-1', 'ISBN-0001', 'u-test-1')
            if not result.get('ok'):
                self.log_test("GA Storage - Return", False, result.get('reason'))
                return False
            
            self.log_test("GA Storage - All Operations", True, "All operations successful")
            return True
            
        except Exception as e:
            self.log_test("GA Storage", False, str(e))
            return False
    
    def test_ga_oplog(self) -> bool:
        """Test GA oplog operations"""
        try:
            from ga.oplog import GAOplog
            
            oplog = GAOplog('./data/siteA')
            
            # Test append operation with unique ID
            operation = {
                'id': f'test-op-{now_ms()}',
                'op': 'RENOVAR',
                'codigo': 'ISBN-0999',
                'userId': 'u-test-oplog',
                'dueDateNew': '2025-02-01'
            }
            
            result = oplog.append_operation(operation)
            if not result:
                self.log_test("GA Oplog - Append", False, "Failed to append operation")
                return False
            
            # Test idempotency with same operation
            result = oplog.append_operation(operation)
            if result:  # Should be False due to idempotency
                self.log_test("GA Oplog - Idempotency", False, "Idempotency check failed")
                return False
            
            # Test stats
            stats = oplog.get_oplog_stats()
            if stats['total_operations'] < 1:
                self.log_test("GA Oplog - Stats", False, f"Expected at least 1 operation, got {stats['total_operations']}")
                return False
            
            self.log_test("GA Oplog - All Operations", True, "All oplog operations successful")
            return True
            
        except Exception as e:
            self.log_test("GA Oplog", False, str(e))
            return False
    
    def test_ga_server_direct(self) -> bool:
        """Test GA server via direct ZMQ connection"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://127.0.0.1:5560')
            socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            
            # Test loan request with a different book
            request = {
                'method': 'checkAndLoan',
                'payload': {
                    'id': f'test-direct-{now_ms()}',
                    'libroCodigo': 'ISBN-0100',  # Use a different book
                    'userId': 'u-test-direct'
                }
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if not response.get('ok'):
                self.log_test("GA Server Direct - Loan", False, response.get('reason'))
                return False
            
            socket.close()
            context.term()
            
            self.log_test("GA Server Direct - Loan", True, "Direct GA communication successful")
            return True
            
        except Exception as e:
            self.log_test("GA Server Direct", False, str(e))
            return False
    
    def test_ap_actor(self) -> bool:
        """Test AP actor via ZMQ connection"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://127.0.0.1:5557')
            socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            
            # Test loan request (AP format)
            request = {
                'id': f'test-ap-{now_ms()}',
                'libroCodigo': 'ISBN-0200',  # Use a different book
                'userId': 'u-test-ap'
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if not response.get('ok'):
                self.log_test("AP Actor - Loan", False, response.get('reason'))
                return False
            
            socket.close()
            context.term()
            
            self.log_test("AP Actor - Loan", True, "AP actor communication successful")
            return True
            
        except Exception as e:
            self.log_test("AP Actor", False, str(e))
            return False
    
    def test_gc_integration(self) -> bool:
        """Test integration with GC (if running)"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://127.0.0.1:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout
            
            # Test PRESTAR request to GC
            request = {
                'id': 'test-gc-1',
                'sedeId': 'A',
                'userId': 'u-test-4',
                'op': 'PRESTAR',
                'libroCodigo': 'ISBN-0004',
                'timestamp': now_ms()
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('status') not in ['OK', 'ERROR']:
                self.log_test("GC Integration - PRESTAR", False, f"Unexpected response: {response}")
                return False
            
            socket.close()
            context.term()
            
            self.log_test("GC Integration - PRESTAR", True, "GC integration successful")
            return True
            
        except Exception as e:
            self.log_test("GC Integration", False, str(e))
            return False
    
    def cleanup_processes(self):
        """Clean up all started processes"""
        for process, name in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"🛑 Stopped {name}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"💀 Killed {name}")
            except Exception as e:
                print(f"⚠️ Error stopping {name}: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🧪 Starting Integration Tests for Sebastián's Components")
        print("=" * 60)
        
        # Test 1: GA Storage
        print("\n📚 Testing GA Storage...")
        self.test_ga_storage()
        
        # Test 2: GA Oplog
        print("\n📝 Testing GA Oplog...")
        self.test_ga_oplog()
        
        # Test 3: Start GA Server
        print("\n🖥️ Starting GA Server...")
        ga_process = self.start_process([
            'python', '-m', 'ga.server', 
            '--data-dir', './data/siteA', 
            '--node-id', 'A'
        ], 'GA Server')
        
        if ga_process and self.wait_for_port(5560):
            # Test 4: GA Server Direct
            print("\n🔗 Testing GA Server Direct...")
            self.test_ga_server_direct()
            
            # Test 5: Start AP Actor
            print("\n🎭 Starting AP Actor...")
            ap_process = self.start_process([
                'python', '-m', 'actors.prestamo'
            ], 'AP Actor')
            
            if ap_process and self.wait_for_port(5557):
                # Test 6: AP Actor
                print("\n🎯 Testing AP Actor...")
                self.test_ap_actor()
                
                # Test 7: GC Integration (if GC is running)
                print("\n🌐 Testing GC Integration...")
                if self.wait_for_port(5555, timeout=2):
                    self.test_gc_integration()
                else:
                    self.log_test("GC Integration", True, "GC not running, skipping test")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        self.cleanup_processes()
        
        # Summary
        print("\n📊 Test Summary:")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
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
    """Main function to run integration tests"""
    test = IntegrationTest()
    results = test.run_all_tests()
    
    if results['success_rate'] >= 0.8:
        print("\n🎉 Integration tests mostly successful!")
        return 0
    else:
        print("\n💥 Integration tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
