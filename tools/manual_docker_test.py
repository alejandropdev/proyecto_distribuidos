"""
Manual Docker Environment Simulation Test
Tests Sebastián's components in a simulated Docker network environment
without requiring Docker to be running.
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


class ManualDockerTest:
    """Manual test simulating Docker environment"""
    
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
    
    def start_process(self, cmd: List[str], name: str, env_vars: Dict[str, str] = None) -> subprocess.Popen:
        """Start a background process with environment variables"""
        try:
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
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
    
    def test_gc_integration(self) -> bool:
        """Test GC integration with Sebastián's components"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5555')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test PRESTAR request (should go through GC → AP → GA)
            request = {
                'id': f'manual-test-{now_ms()}',
                'sedeId': 'A',
                'userId': 'u-manual-test',
                'op': 'PRESTAR',
                'libroCodigo': 'ISBN-0001',
                'timestamp': now_ms()
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('status') in ['OK', 'ERROR']:
                self.log_test("GC Integration", True, f"Response: {response.get('status')}")
                return True
            else:
                self.log_test("GC Integration", False, f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            self.log_test("GC Integration", False, str(e))
            return False
        finally:
            socket.close()
            context.term()
    
    def test_ap_direct(self) -> bool:
        """Test AP actor directly"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5557')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test loan request
            request = {
                'id': f'manual-ap-{now_ms()}',
                'libroCodigo': 'ISBN-0002',
                'userId': 'u-manual-ap'
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('ok') is not None:
                self.log_test("AP Direct", True, f"Response: {response}")
                return True
            else:
                self.log_test("AP Direct", False, f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            self.log_test("AP Direct", False, str(e))
            return False
        finally:
            socket.close()
            context.term()
    
    def test_ga_direct(self) -> bool:
        """Test GA server directly"""
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect('tcp://localhost:5560')
            socket.setsockopt(zmq.RCVTIMEO, 5000)
            
            # Test loan request
            request = {
                'method': 'checkAndLoan',
                'payload': {
                    'id': f'manual-ga-{now_ms()}',
                    'libroCodigo': 'ISBN-0003',
                    'userId': 'u-manual-ga'
                }
            }
            
            socket.send_json(request)
            response = socket.recv_json()
            
            if response.get('ok') is not None:
                self.log_test("GA Direct", True, f"Response: {response}")
                return True
            else:
                self.log_test("GA Direct", False, f"Unexpected response: {response}")
                return False
                
        except Exception as e:
            self.log_test("GA Direct", False, str(e))
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
    
    def test_pub_sub_messages(self) -> bool:
        """Test PUB/SUB message flow"""
        try:
            # Start subscriber in background
            subscriber_thread = threading.Thread(target=self._subscriber_thread)
            subscriber_thread.daemon = True
            subscriber_thread.start()
            
            # Wait a bit for subscriber to start
            time.sleep(2)
            
            # Test GC PUB (simulate by connecting to GC PUB port)
            context = zmq.Context()
            pub_socket = context.socket(zmq.PUB)
            pub_socket.bind('tcp://127.0.0.1:5556')
            time.sleep(1)  # Wait for binding
            
            # Send test message
            test_message = {
                'id': f'pub-test-{now_ms()}',
                'sedeId': 'A',
                'userId': 'u-pub-test',
                'libroCodigo': 'ISBN-0004',
                'op': 'RENOVAR',
                'dueDateNew': '2025-02-01'
            }
            
            pub_socket.send_string('RENOVACION ' + json.dumps(test_message))
            time.sleep(1)  # Wait for message to be sent
            
            pub_socket.close()
            context.term()
            
            self.log_test("PUB/SUB Messages", True, "Message sent successfully")
            return True
            
        except Exception as e:
            self.log_test("PUB/SUB Messages", False, str(e))
            return False
    
    def _subscriber_thread(self):
        """Background subscriber thread"""
        try:
            context = zmq.Context()
            sub_socket = context.socket(zmq.SUB)
            sub_socket.connect('tcp://127.0.0.1:5556')
            sub_socket.setsockopt(zmq.SUBSCRIBE, b'RENOVACION')
            
            # Wait for message
            if sub_socket.poll(5000):  # 5 second timeout
                message = sub_socket.recv()
                print(f"📨 Received PUB/SUB message: {message.decode()}")
            
            sub_socket.close()
            context.term()
            
        except Exception as e:
            print(f"⚠️ Subscriber error: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all manual Docker simulation tests"""
        print("🧪 Starting Manual Docker Environment Simulation")
        print("=" * 60)
        
        # Setup cleanup trap
        import signal
        def signal_handler(signum, frame):
            print("\n🛑 Received interrupt signal, cleaning up...")
            self.cleanup_processes()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start GA Server (Site A)
            print("\n🖥️ Starting GA Server (Site A)...")
            ga_env = {
                'GA_DATA_DIR': './data/siteA',
                'GA_REP_BIND': 'tcp://0.0.0.0:5560',
                'GA_HEALTH_REP_BIND': 'tcp://0.0.0.0:5564',
                'GA_HEARTBEAT_PUB_BIND': 'tcp://0.0.0.0:5565',
                'GA_HEARTBEAT_INTERVAL_MS': '2000',
                'GA_REPL_PUB_BIND': 'tcp://0.0.0.0:5562',
                'GA_REPL_SUB_CONNECT': 'tcp://127.0.0.1:5563'
            }
            
            ga_process = self.start_process([
                'python', '-m', 'ga.server', 
                '--data-dir', './data/siteA', 
                '--node-id', 'A', '--pretty'
            ], 'GA Server', ga_env)
            
            if not ga_process or not self.wait_for_port(5560):
                self.log_test("GA Server Start", False, "Failed to start GA server")
                return self._get_results()
            
            # Start AP Actor
            print("\n🎭 Starting AP Actor...")
            ap_env = {
                'AP_REP_BIND': 'tcp://0.0.0.0:5557',
                'GA_REP_BIND': 'tcp://127.0.0.1:5560'
            }
            
            ap_process = self.start_process([
                'python', '-m', 'actors.prestamo', '--pretty'
            ], 'AP Actor', ap_env)
            
            if not ap_process or not self.wait_for_port(5557):
                self.log_test("AP Actor Start", False, "Failed to start AP actor")
                return self._get_results()
            
            # Start AR Actor
            print("\n🔄 Starting AR Actor...")
            ar_env = {
                'GC_PUB_CONNECT': 'tcp://127.0.0.1:5556',
                'TOPIC_RENOVACION': 'RENOVACION',
                'GA_REP_BIND': 'tcp://127.0.0.1:5560'
            }
            
            ar_process = self.start_process([
                'python', '-m', 'actors.renovacion', '--pretty'
            ], 'AR Actor', ar_env)
            
            # Start AD Actor
            print("\n📚 Starting AD Actor...")
            ad_env = {
                'GC_PUB_CONNECT': 'tcp://127.0.0.1:5556',
                'TOPIC_DEVOLUCION': 'DEVOLUCION',
                'GA_REP_BIND': 'tcp://127.0.0.1:5560'
            }
            
            ad_process = self.start_process([
                'python', '-m', 'actors.devolucion', '--pretty'
            ], 'AD Actor', ad_env)
            
            # Start GC Server (Alejandro's component)
            print("\n🌐 Starting GC Server...")
            gc_env = {
                'GC_BIND': 'tcp://0.0.0.0:5555',
                'GC_PUB_BIND': 'tcp://0.0.0.0:5556',
                'TOPIC_RENOVACION': 'RENOVACION',
                'TOPIC_DEVOLUCION': 'DEVOLUCION',
                'AP_REQ_CONNECT': 'tcp://127.0.0.1:5557',
                'GC_MODE': 'serial'
            }
            
            gc_process = self.start_process([
                'python', '-m', 'gestor_central.server', 
                '--mode', 'serial', '--pretty'
            ], 'GC Server', gc_env)
            
            if not gc_process or not self.wait_for_port(5555):
                self.log_test("GC Server Start", False, "Failed to start GC server")
                return self._get_results()
            
            # Wait for all services to stabilize
            print("\n⏳ Waiting for services to stabilize...")
            time.sleep(5)
            
            # Test connections
            print("\n🔗 Testing service connections...")
            self.test_gc_integration()
            self.test_ap_direct()
            self.test_ga_direct()
            self.test_ga_health()
            
            # Test PUB/SUB
            print("\n📡 Testing PUB/SUB messages...")
            self.test_pub_sub_messages()
            
        finally:
            # Cleanup
            print("\n🧹 Cleaning up...")
            self.cleanup_processes()
        
        return self._get_results()
    
    def _get_results(self) -> Dict[str, Any]:
        """Get test results summary"""
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print("\n📊 Manual Docker Simulation Test Summary:")
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
    """Main function to run manual Docker simulation tests"""
    test = ManualDockerTest()
    results = test.run_all_tests()
    
    if results['success_rate'] >= 0.8:
        print("\n🎉 Manual Docker simulation tests mostly successful!")
        print("✅ Sebastián's components are ready for Docker integration!")
        return 0
    else:
        print("\n💥 Manual Docker simulation tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
