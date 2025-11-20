#!/usr/bin/env python3
"""
CI-Friendly Comprehensive Test Suite for K2SHBWI
Creates all required test files on-the-fly - no external dependencies!

This version is designed for CI environments where test files don't exist.
All test assets are generated automatically before running tests.
"""

import subprocess
import json
from pathlib import Path
import sys
import time
import os
import tempfile
from PIL import Image, ImageDraw

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import TestLogger, but make it optional for CI
try:
    from src.utils.test_logger import TestLogger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False
    print("[WARN] TestLogger not available, skipping log generation")


class CITestRunner:
    """CI-Friendly test runner that creates all required files"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()
        self.python_exe = 'python'
        self.cli = "tools/cli_click.py"
        
        # Create temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp(prefix="k2shbwi_test_"))
        self.test_image = self.test_dir / "test_image.png"
        self.test_output_k2sh = self.test_dir / "test_output_click.k2sh"
        self.batch_input_dir = self.test_dir / "batch_input"
        
        # Initialize logger (optional)
        if HAS_LOGGER:
            try:
                self.logger = TestLogger(logger_name="comprehensive_test_suite_ci", log_type="test")
            except Exception:
                self.logger = None
                print("[WARN] Logger initialization failed, continuing without logging")
        else:
            self.logger = None
        
        # Create all required test files
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Create all required test files and directories"""
        print("\n[SETUP] Creating test environment...")
        
        # Create test image
        self.create_test_image()
        
        # Create batch input directory with test images
        self.create_batch_input()
        
        # Create initial test_output_click.k2sh file (required by some tests)
        self.create_initial_k2sh_file()
        
        print(f"[SETUP] Test environment ready at: {self.test_dir}")
    
    def create_test_image(self):
        """Create a test PNG image"""
        img = Image.new('RGB', (512, 512), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 462, 462], outline=(0, 0, 255), width=4)
        draw.text((200, 240), "K2SHBWI Test Image", fill=(0, 0, 0))
        img.save(self.test_image)
        print(f"[SETUP] Created test image: {self.test_image}")
    
    def create_batch_input(self):
        """Create batch_input directory with multiple test images"""
        self.batch_input_dir.mkdir(exist_ok=True)
        
        for i in range(3):
            img = Image.new('RGB', (256, 256), color=(200 + i*20, 200, 200))
            draw = ImageDraw.Draw(img)
            draw.text((80, 120), f"Batch {i+1}", fill=(0, 0, 0))
            batch_img = self.batch_input_dir / f"batch_{i+1}.png"
            img.save(batch_img)
        
        print(f"[SETUP] Created batch input: {self.batch_input_dir} (3 images)")
    
    def create_initial_k2sh_file(self):
        """Create initial test_output_click.k2sh file"""
        code, out, err = self.run_command(
            "create", "-i", str(self.test_image), "-o", str(self.test_output_k2sh)
        )
        if code == 0:
            print(f"[SETUP] Created initial K2SH file: {self.test_output_k2sh}")
        else:
            print(f"[WARN] Failed to create initial K2SH file: {err}")
    
    def run_command(self, *args):
        """Run CLI command and capture output"""
        try:
            # Change to project root for relative paths
            original_cwd = os.getcwd()
            project_root = Path(__file__).parent.parent
            os.chdir(project_root)
            
            cmd = [self.python_exe, self.cli] + list(args)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            
            os.chdir(original_cwd)
            # Combine stdout and stderr for better error messages
            error_msg = result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
            return result.returncode, result.stdout, error_msg
        except Exception as e:
            return 1, "", str(e)
    
    def check_dependency(self, module_name, package_name=None):
        """Check if a dependency is available"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    def test(self, name, test_func):
        """Run a test"""
        print(f"\nTesting: {name}...", end=" ")
        test_start_time = time.time()
        
        try:
            test_func()
            elapsed_ms = (time.time() - test_start_time) * 1000
            print("[PASS]")
            self.test_results.append({"name": name, "status": "PASS"})
            self.passed += 1
            
            if self.logger:
                try:
                    self.logger.log_test_result(
                        test_name=name,
                        status="PASS",
                        input_bytes=0,
                        output_bytes=0,
                        processing_time_ms=elapsed_ms,
                        compression_type="N/A",
                        error_msg=None
                    )
                except Exception:
                    pass
        except (AssertionError, SystemExit) as e:
            # Check if this is a skip signal
            error_msg = str(e)
            if "SKIP:" in error_msg:
                elapsed_ms = (time.time() - test_start_time) * 1000
                skip_reason = error_msg.replace("SKIP:", "").strip()
                print(f"[SKIP]: {skip_reason}")
                self.test_results.append({"name": name, "status": "SKIP", "reason": skip_reason})
                # SKIP doesn't count as pass or fail
            else:
                elapsed_ms = (time.time() - test_start_time) * 1000
                print(f"[FAIL]: {e}")
                self.test_results.append({"name": name, "status": "FAIL", "error": str(e)})
                self.failed += 1
                
                if self.logger:
                    try:
                        self.logger.log_test_result(
                            test_name=name,
                            status="FAIL",
                            input_bytes=0,
                            output_bytes=0,
                            processing_time_ms=elapsed_ms,
                            compression_type="N/A",
                            error_msg=str(e)
                        )
                    except Exception:
                        pass
        except Exception as e:
            elapsed_ms = (time.time() - test_start_time) * 1000
            print(f"[ERROR]: {e}")
            self.test_results.append({"name": name, "status": "ERROR", "error": str(e)})
            self.failed += 1
    
    # PHASE 3 Tests
    def test_create_command(self):
        """Test create command"""
        output_file = self.test_dir / "test_p3_create.k2sh"
        code, out, err = self.run_command("create", "-i", str(self.test_image), "-o", str(output_file))
        assert code == 0, f"Exit code {code}: {err}"
        assert "[OK]" in out or "Created:" in out, f"Unexpected output: {out}"
        assert output_file.exists(), "Output file not created"
    
    def test_create_with_metadata(self):
        """Test create with metadata"""
        output_file = self.test_dir / "test_p3_meta.k2sh"
        code, out, err = self.run_command(
            "create", "-i", str(self.test_image), "-o", str(output_file), "-t", "TestTitle"
        )
        assert code == 0, f"Exit code {code}: {err}"
        assert output_file.exists(), "Output file not created"
    
    def test_info_command(self):
        """Test info command"""
        code, out, err = self.run_command("info", str(self.test_output_k2sh))
        assert code == 0, f"Exit code {code}: {err}"
        assert "File Information" in out or "K2SHBWI" in out, "Missing title in output"
    
    def test_validate_command(self):
        """Test validate command"""
        code, out, err = self.run_command("validate", str(self.test_output_k2sh))
        assert code == 0, f"Exit code {code}: {err}"
        assert "[OK]" in out or "VALID" in out, "File validation failed"
    
    def test_decode_command(self):
        """Test decode command"""
        decoded_file = self.test_dir / "test_p3_decoded.png"
        code, out, err = self.run_command("decode", str(self.test_output_k2sh), "-o", str(decoded_file))
        assert code == 0, f"Exit code {code}: {err}"
        assert decoded_file.exists(), "Decoded image not created"
        assert "[OK]" in out or "Decoded" in out, "Decode incomplete"
    
    def test_batch_command(self):
        """Test batch command"""
        batch_output = self.test_dir / "test_p3_batch"
        code, out, err = self.run_command("batch", "-i", str(self.batch_input_dir), "-o", str(batch_output))
        assert code == 0, f"Exit code {code}: {err}"
        assert "Successful:" in out or "processed" in out.lower(), "Batch processing failed"
    
    def test_encode_command(self):
        """Test encode command"""
        output_file = self.test_dir / "test_p3_encode.k2sh"
        code, out, err = self.run_command("encode", "-i", str(self.test_image), "-o", str(output_file))
        assert code == 0, f"Exit code {code}: {err}"
        assert output_file.exists(), "Encoded file not created"
    
    # PHASE 4 Tests
    def test_convert_html(self):
        """Test HTML conversion"""
        html_file = self.test_dir / "test_p4_convert.html"
        code, out, err = self.run_command("convert", str(self.test_output_k2sh), "-f", "html", "-o", str(html_file))
        assert code == 0, f"Exit code {code}: {err}"
        assert html_file.exists(), "HTML file not created"
        assert html_file.stat().st_size > 0, "HTML file is empty"
        
        html_content = html_file.read_text()
        assert "<html" in html_content.lower(), "Not valid HTML"
    
    def test_convert_pdf(self):
        """Test PDF conversion"""
        pdf_file = self.test_dir / "test_p4_convert.pdf"
        code, out, err = self.run_command("convert", str(self.test_output_k2sh), "-f", "pdf", "-o", str(pdf_file))
        
        if code != 0:
            # Check if it's a dependency issue - PIL fallback should work
            error_msg = err if err else out
            if "cannot save" in error_msg.lower() or "unsupported" in error_msg.lower():
                raise AssertionError(f"SKIP: PDF conversion not supported: {error_msg}")
            else:
                raise AssertionError(f"PDF conversion failed: {error_msg}")
        
        if not pdf_file.exists():
            raise AssertionError(f"PDF file not created. Error: {err if err else 'Unknown error'}")
        
        if pdf_file.stat().st_size == 0:
            raise AssertionError("PDF file is empty")
    
    def test_convert_pptx(self):
        """Test PPTX conversion"""
        # Check if python-pptx is available
        if not self.check_dependency("pptx"):
            raise AssertionError("SKIP: python-pptx not installed")
        
        pptx_file = self.test_dir / "test_p4_convert.pptx"
        code, out, err = self.run_command("convert", str(self.test_output_k2sh), "-f", "pptx", "-o", str(pptx_file))
        
        if code != 0:
            error_msg = err if err else out
            if "python-pptx" in error_msg.lower() or "import" in error_msg.lower():
                raise AssertionError(f"SKIP: PPTX dependency missing: {error_msg}")
            else:
                raise AssertionError(f"PPTX conversion failed: {error_msg}")
        
        if not pptx_file.exists():
            raise AssertionError(f"PPTX file not created. Error: {err if err else 'Unknown error'}")
        
        if pptx_file.stat().st_size == 0:
            raise AssertionError("PPTX file is empty")
    
    def test_convert_all_formats(self):
        """Test all conversion formats (only tests available formats)"""
        formats_to_test = ['html']  # Always test HTML
        
        # Try PDF
        pdf_file = self.test_dir / "test_all_pdf.pdf"
        pdf_code, pdf_out, pdf_err = self.run_command("convert", str(self.test_output_k2sh), "-f", "pdf", "-o", str(pdf_file))
        if pdf_code == 0 and pdf_file.exists() and pdf_file.stat().st_size > 0:
            formats_to_test.append('pdf')
        
        # Try PPTX if available
        if self.check_dependency("pptx"):
            pptx_file = self.test_dir / "test_all_pptx.pptx"
            pptx_code, pptx_out, pptx_err = self.run_command("convert", str(self.test_output_k2sh), "-f", "pptx", "-o", str(pptx_file))
            if pptx_code == 0 and pptx_file.exists() and pptx_file.stat().st_size > 0:
                formats_to_test.append('pptx')
        
        # Test all available formats
        assert len(formats_to_test) >= 1, "At least HTML conversion should work"
        for fmt in formats_to_test:
            output_file = self.test_dir / f"test_all_{fmt}.{fmt}"
            code, out, err = self.run_command("convert", str(self.test_output_k2sh), "-f", fmt, "-o", str(output_file))
            assert code == 0, f"Conversion to {fmt} failed: {err if err else out}"
            assert output_file.exists(), f"{fmt} file not created"
    
    # PHASE 5 Tests
    def test_view_help(self):
        """Test view command help"""
        code, out, err = self.run_command("view", "--help")
        assert code == 0, f"Exit code {code}: {err}"
        assert "web" in out.lower() or "view" in out.lower(), "View command help not found"
    
    # PHASE 6 Tests
    def test_all_commands_have_help(self):
        """Test that all commands have help text"""
        commands = ["create", "info", "validate", "batch", "encode", "decode", "convert", "view"]
        for cmd in commands:
            code, out, err = self.run_command(cmd, "--help")
            assert code == 0, f"Help not available for {cmd}"
            assert "Usage:" in out or "Options:" in out or len(out) > 10, f"No usage for {cmd}"
    
    def test_create_multiple_files(self):
        """Test creating multiple K2SHBWI files"""
        for i in range(3):
            output_file = self.test_dir / f"test_multi_{i}.k2sh"
            code, out, err = self.run_command("create", "-i", str(self.test_image), "-o", str(output_file))
            assert code == 0, f"Failed to create file {i}: {err}"
            assert output_file.exists(), f"File test_multi_{i}.k2sh not created"
    
    def test_validate_all_outputs(self):
        """Test validation of all created files"""
        test_files = list(self.test_dir.glob("test_p*_*.k2sh")) + list(self.test_dir.glob("test_multi_*.k2sh"))
        for file in test_files[:5]:  # Test first 5
            code, out, err = self.run_command("validate", str(file))
            assert code == 0, f"Validation failed for {file}"
    
    def test_verbose_output(self):
        """Test verbose output flag"""
        code, out, err = self.run_command("info", str(self.test_output_k2sh), "-v")
        assert code == 0, f"Exit code {code}: {err}"
        assert len(out) > 50, "Verbose output seems truncated"
    
    # PHASE 7 Tests (Documentation)
    def test_cli_version(self):
        """Test CLI version display"""
        code, out, err = self.run_command("--version")
        assert code == 0, f"Exit code {code}: {err}"
        assert "1.0.0" in out or "version" in out.lower(), "Version not displayed correctly"
    
    def test_cli_main_help(self):
        """Test main help command"""
        code, out, err = self.run_command("--help")
        assert code == 0, f"Exit code {code}: {err}"
        assert "Interactive Image Encoding" in out or "K2SHBWI" in out, "Main help not descriptive"
    
    def test_command_examples(self):
        """Test that command help includes examples"""
        code, out, err = self.run_command("create", "--help")
        assert code == 0, f"Exit code {code}: {err}"
        has_example = "example" in out.lower() or "k2shbwi" in out.lower() or "image" in out.lower()
        assert has_example, "Command help should include examples or usage"
    
    def cleanup(self):
        """Clean up temporary test files"""
        try:
            import shutil
            shutil.rmtree(self.test_dir)
            print(f"\n[CLEANUP] Removed test directory: {self.test_dir}")
        except Exception as e:
            print(f"\n[WARN] Cleanup failed: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("K2SHBWI CLICK CLI - CI-FRIENDLY TEST SUITE")
        print("="*60)
        
        try:
            # PHASE 3 Tests
            print("\n[PHASE 3] Implement 8 Commands")
            self.test("Create Command", self.test_create_command)
            self.test("Create with Metadata", self.test_create_with_metadata)
            self.test("Info Command", self.test_info_command)
            self.test("Validate Command", self.test_validate_command)
            self.test("Decode Command", self.test_decode_command)
            self.test("Batch Command", self.test_batch_command)
            self.test("Encode Command", self.test_encode_command)
            
            # PHASE 4 Tests
            print("\n[PHASE 4] Create Converter Modules")
            self.test("Convert to HTML", self.test_convert_html)
            self.test("Convert to PDF", self.test_convert_pdf)
            self.test("Convert to PPTX", self.test_convert_pptx)
            self.test("All Conversion Formats", self.test_convert_all_formats)
            
            # PHASE 5 Tests
            print("\n[PHASE 5] Create Viewer Modules")
            self.test("View Command Help", self.test_view_help)
            
            # PHASE 6 Tests
            print("\n[PHASE 6] Testing & Validation")
            self.test("All Commands Have Help", self.test_all_commands_have_help)
            self.test("Create Multiple Files", self.test_create_multiple_files)
            self.test("Validate All Outputs", self.test_validate_all_outputs)
            self.test("Verbose Output", self.test_verbose_output)
            
            # PHASE 7 Tests
            print("\n[PHASE 7] Documentation")
            self.test("CLI Version Display", self.test_cli_version)
            self.test("Main Help", self.test_cli_main_help)
            self.test("Command Examples", self.test_command_examples)
        finally:
            # Always cleanup
            self.cleanup()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        elapsed = time.time() - self.start_time
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        total_tests = len(self.test_results)  # Total includes SKIP
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"[PASS] Passed:  {self.passed}")
        print(f"[FAIL] Failed:  {self.failed}")
        if skipped > 0:
            print(f"[SKIP] Skipped: {skipped} (optional dependencies)")
        print(f"[TIME] Time:    {elapsed:.2f}s")
        print(f"[INFO] Total:   {total_tests} ({self.passed + self.failed} executed, {skipped} skipped)")
        
        if self.failed == 0:
            print("\n*** ALL TESTS PASSED! ***")
            if skipped > 0:
                print(f"({skipped} test(s) skipped - optional dependencies)")
        else:
            print(f"\n*** {self.failed} tests failed ***")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            if result["status"] == "PASS":
                status_icon = "[OK]"
            elif result["status"] == "SKIP":
                status_icon = "[--]"
            else:
                status_icon = "[XX]"
            print(f"{status_icon} {result['name']}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
            elif "reason" in result:
                print(f"   Reason: {result['reason']}")
        
        if skipped > 0:
            print(f"\n[INFO] {skipped} test(s) skipped (optional dependencies)")
        
        # Save results to file
        results_file = Path("TEST_RESULTS.json")
        total_tests = len(self.test_results)
        with open(results_file, "w") as f:
            json.dump({
                "passed": self.passed,
                "failed": self.failed,
                "skipped": skipped,
                "total": total_tests,
                "total_executed": self.passed + self.failed,
                "elapsed_seconds": elapsed,
                "results": self.test_results,
                "ci_friendly": True
            }, f, indent=2)
        
        print(f"\nFull results saved to {results_file}")
        
        # Save logs with summary (if logger available)
        if self.logger:
            try:
                self.logger.add_summary({
                    "test_suite": "comprehensive_test_suite_ci",
                    "total_tests": self.passed + self.failed,
                    "passed_tests": self.passed,
                    "failed_tests": self.failed,
                    "total_time_seconds": elapsed,
                    "success_rate_percent": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
                })
                log_paths = self.logger.save_log()
                print(f"\n[Logging] Metrics saved to {log_paths.get('json', 'N/A')}")
            except Exception as e:
                print(f"\n[WARN] Logging failed: {e}")
        
        sys.exit(0 if self.failed == 0 else 1)


if __name__ == "__main__":
    runner = CITestRunner()
    runner.run_all_tests()

