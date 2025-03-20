import asyncio
import aiohttp
import time
import logging
import statistics
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Tuple
import json
import os
from datetime import datetime

class APIStressTester:
    """
    Stress tests the API for performance
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize the API stress tester
        
        Args:
            base_url (str): Base URL of the API
            username (str): API username
            password (str): API password
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.logger = logging.getLogger(__name__)
    
    async def login(self) -> bool:
        """
        Login to the API and get access token
        
        Returns:
            bool: True if login successful
        """
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    "username": self.username,
                    "password": self.password
                }
                
                async with session.post(f"{self.base_url}/token", data=login_data) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        self.token = response_data.get("access_token")
                        return True
                    else:
                        self.logger.error(f"Login failed: {response.status}", exc_info=True)
                        return False
        except Exception as e:
            self.logger.error(f"Error during login: {str(e)}", exc_info=True)
            return False
    
    async def test_endpoint(
        self, 
        endpoint: str, 
        method: str = "GET", 
        data: Dict = None, 
        num_requests: int = 100, 
        concurrency: int = 10
    ) -> Dict[str, Any]:
        """
        Test an API endpoint with multiple concurrent requests
        
        Args:
            endpoint (str): API endpoint to test
            method (str): HTTP method (GET, POST, etc.)
            data (Dict, optional): Request data for POST/PUT requests
            num_requests (int): Total number of requests to make
            concurrency (int): Number of concurrent requests
            
        Returns:
            Dict[str, Any]: Test results
        """
        if not self.token:
            if not await self.login():
                return {"error": "Failed to login"}
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Prepare tasks
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def make_request():
            async with semaphore:
                start_time = time.time()
                status_code = None
                error = None
                
                try:
                    async with aiohttp.ClientSession() as session:
                        if method == "GET":
                            async with session.get(url, headers=headers) as response:
                                status_code = response.status
                                await response.text()
                        elif method == "POST":
                            async with session.post(url, headers=headers, json=data) as response:
                                status_code = response.status
                                await response.text()
                        elif method == "PUT":
                            async with session.put(url, headers=headers, json=data) as response:
                                status_code = response.status
                                await response.text()
                        elif method == "DELETE":
                            async with session.delete(url, headers=headers) as response:
                                status_code = response.status
                                await response.text()
                except Exception as e:
                    error = str(e)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                return {
                    "status_code": status_code,
                    "response_time": response_time,
                    "error": error
                }
        
        for _ in range(num_requests):
            tasks.append(asyncio.ensure_future(make_request()))
        
        # Run tasks
        self.logger.info(f"Starting stress test for {endpoint} with {num_requests} requests ({concurrency} concurrent)")
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Calculate metrics
        total_time = end_time - start_time
        successful_requests = sum(1 for r in responses if r["status_code"] == 200)
        failed_requests = num_requests - successful_requests
        
        response_times = [r["response_time"] for r in responses if r["status_code"] == 200]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        requests_per_second = num_requests / total_time if total_time > 0 else 0
        
        return {
            "endpoint": endpoint,
            "method": method,
            "total_requests": num_requests,
            "concurrency": concurrency,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time_seconds": total_time,
            "requests_per_second": requests_per_second,
            "response_times_ms": {
                "average": avg_response_time,
                "min": min_response_time,
                "max": max_response_time,
                "p95": p95_response_time,
                "p99": p99_response_time
            },
            "status_code_distribution": self._count_status_codes(responses)
        }
    
    def _count_status_codes(self, responses: List[Dict[str, Any]]) -> Dict[int, int]:
        """
        Count occurrences of each status code
        
        Args:
            responses (List[Dict[str, Any]]): List of response data
            
        Returns:
            Dict[int, int]: Count of each status code
        """
        status_counts = {}
        
        for response in responses:
            status_code = response["status_code"]
            if status_code:
                status_counts[status_code] = status_counts.get(status_code, 0) + 1
        
        return status_counts
    
    def plot_results(self, results: Dict[str, Any], output_file: str = None):
        """
        Plot stress test results
        
        Args:
            results (Dict[str, Any]): Test results
            output_file (str, optional): Path to save the plot
        """
        if "error" in results:
            self.logger.error("Cannot plot results: Invalid results data", exc_info=True)
            return
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Plot response time distribution
        response_times = results["response_times_ms"]
        metrics = ["average", "min", "max", "p95", "p99"]
        values = [response_times[m] for m in metrics]
        
        ax1.bar(metrics, values, color='skyblue')
        ax1.set_title('Response Time (ms)')
        ax1.set_ylabel('Time (ms)')
        
        # Plot status code distribution
        status_codes = list(results["status_code_distribution"].keys())
        counts = list(results["status_code_distribution"].values())
        
        ax2.bar(status_codes, counts, color='lightgreen')
        ax2.set_title('Status Code Distribution')
        ax2.set_ylabel('Count')
        
        # Add overall metrics as text
        fig.text(
            0.5, 0.01, 
            f"Endpoint: {results['endpoint']} | Method: {results['method']} | "
            f"Concurrency: {results['concurrency']}\n"
            f"Requests/sec: {results['requests_per_second']:.2f} | "
            f"Success Rate: {results['successful_requests']/results['total_requests']*100:.2f}% | "
            f"Total Time: {results['total_time_seconds']:.2f}s",
            ha='center', fontsize=12
        )
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        if output_file:
            plt.savefig(output_file)
            plt.close()
        else:
            plt.show()

async def run_stress_tests():
    """
    Run stress tests on all API endpoints
    """
    # Initialize components
    from config.settings import Settings
    settings = Settings()
    
    base_url = "http://localhost:8000"  # Update with your API URL
    username = settings.api_username
    password = settings.api_password
    
    # Initialize tester
    tester = APIStressTester(base_url, username, password)
    
    # Create output directory
    output_dir = "stress_test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Define test scenarios
    test_scenarios = [
        # Endpoint, Method, Data, Num Requests, Concurrency
        ("/api/symbols", "GET", None, 100, 10),
        ("/api/analysis", "GET", None, 50, 5),
        ("/api/analysis/sentiment", "GET", None, 100, 10),
        ("/api/symbols", "POST", {"symbol": "BTC-USDT"}, 20, 5),
        ("/api/config", "GET", None, 100, 10)
    ]
    
    # Run tests
    for endpoint, method, data, num_requests, concurrency in test_scenarios:
        results = await tester.test_endpoint(
            endpoint=endpoint,
            method=method,
            data=data,
            num_requests=num_requests,
            concurrency=concurrency
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/{method}_{endpoint.replace('/', '_')}_{timestamp}"
        
        with open(f"{filename}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        tester.plot_results(results, output_file=f"{filename}.png")
        
        # Log results
        logging.info(f"Completed stress test for {method} {endpoint}")
        logging.info(f"  Requests/sec: {results['requests_per_second']:.2f}")
        logging.info(f"  Avg response time: {results['response_times_ms']['average']:.2f} ms")
        logging.info(f"  Success rate: {results['successful_requests']/results['total_requests']*100:.2f}%")
        
        # Wait a bit between tests
        await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(run_stress_tests())
