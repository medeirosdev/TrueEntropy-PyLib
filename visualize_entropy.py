import sys
import time
import math
import logging
import threading
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    filename='visualization_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("visualizer")

try:
    import pygame
except ImportError:
    print("Error: Pygame is not installed. Please install it with 'pip install pygame'")
    logger.error("Pygame not found")
    sys.exit(1)

# TrueEntropy Imports
try:
    from trueentropy.pool import EntropyPool
    from trueentropy.harvesters.base import BaseHarvester, HarvestResult
    from trueentropy.harvesters.timing import TimingHarvester
    from trueentropy.harvesters.system import SystemHarvester
    from trueentropy.hybrid import HybridTap
    from trueentropy.health import entropy_health # Health Monitor
    
    try:
        from trueentropy.harvesters.network import NetworkHarvester
        HAS_NETWORK = True
    except ImportError:
        HAS_NETWORK = False
        
    try:
        from trueentropy.harvesters.external import ExternalHarvester
        HAS_EXTERNAL = True
    except ImportError:
        HAS_EXTERNAL = False
        
except ImportError as e:
    print(f"Error importing TrueEntropy modules: {e}")
    logger.error(f"Import error: {e}")
    sys.exit(1)

# Configuration
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 850 # Increased height for health section
FPS = 60
POOL_SIZE = 4096  
MAX_BITS = POOL_SIZE * 8

# Colors
COLOR_BG = (15, 20, 25)
COLOR_TEXT = (220, 230, 240)
COLOR_TEXT_DIM = (120, 130, 140)
COLOR_POOL_FILL = (0, 255, 180)
COLOR_POOL_EMPTY = (30, 40, 50)
COLOR_ACCENT = (255, 120, 120)
COLOR_HARVESTER_ACTIVE = (100, 255, 100)
COLOR_HARVESTER_WAITING = (100, 100, 255)
COLOR_HARVESTER_ERROR = (255, 80, 80)
COLOR_HARVESTER_INACTIVE = (60, 70, 80)
COLOR_BTN_BG = (50, 60, 70)
COLOR_BTN_HOVER = (70, 80, 90)
COLOR_BTN_ACTIVE = (80, 180, 100)
COLOR_BTN_ACTIVE_HOVER = (100, 200, 120)
COLOR_HIST_BAR = (80, 150, 255)
COLOR_HIST_GOOD = (100, 255, 100)
COLOR_HIST_BAD = (255, 100, 100)
COLOR_HEALTH_OK = (100, 255, 100)
COLOR_HEALTH_WARN = (255, 200, 50)
COLOR_HEALTH_CRIT = (255, 50, 50)

@dataclass
class HarvesterStatus:
    name: str
    last_bits: int
    last_run: float
    status: str  # "IDLE", "COLLECTING", "SUCCESS", "ERROR"
    enabled: bool = True
    error_msg: str = ""

class VisualizationCollector:
    def __init__(self, pool: EntropyPool):
        self.pool = pool
        self.harvesters: List[BaseHarvester] = []
        self.statuses: Dict[str, HarvesterStatus] = {}
        self.offline_mode = False
        
        # Initialize harvesters
        self._add_harvester(TimingHarvester())
        self._add_harvester(SystemHarvester())
        if HAS_NETWORK:
            self._add_harvester(NetworkHarvester())
        if HAS_EXTERNAL:
            self._add_harvester(ExternalHarvester())
            
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def _add_harvester(self, harvester: BaseHarvester):
        self.harvesters.append(harvester)
        self.statuses[harvester.name] = HarvesterStatus(
            name=harvester.name,
            last_bits=0,
            last_run=0,
            status="IDLE",
            enabled=True
        )

    def toggle_harvester(self, name: str):
        with self.lock:
            if name in self.statuses:
                self.statuses[name].enabled = not self.statuses[name].enabled

    def set_offline_mode(self, enabled: bool):
        self.offline_mode = enabled

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _loop(self):
        while self.running:
            for harvester in self.harvesters:
                if not self.running: break
                
                # Check control flags
                with self.lock:
                    status = self.statuses[harvester.name]
                    is_enabled = status.enabled
                
                # Global offline override for network harvesters
                if self.offline_mode and harvester.name in ["network", "external", "weather"]:
                    continue

                if not is_enabled:
                    with self.lock:
                        self.statuses[harvester.name].status = "DISABLED"
                    continue

                with self.lock:
                    self.statuses[harvester.name].status = "COLLECTING"
                
                # Collect
                try:
                    result = harvester.safe_collect()
                    
                    with self.lock:
                        if result.success:
                            self.statuses[harvester.name].status = "SUCCESS"
                            self.statuses[harvester.name].last_bits = result.entropy_bits
                            self.statuses[harvester.name].last_run = time.time()
                            self.pool.feed(result.data, entropy_estimate=result.entropy_bits)
                        else:
                            self.statuses[harvester.name].status = "ERROR"
                            self.statuses[harvester.name].error_msg = str(result.error)
                except Exception as e:
                    logger.error(f"Error in harvester {harvester.name}: {e}")
                    with self.lock:
                        self.statuses[harvester.name].status = "ERROR"
                        self.statuses[harvester.name].error_msg = str(e)
                
                time.sleep(0.05) 
            
            time.sleep(0.5)

class Button:
    def __init__(self, rect, text, callback, togglable=True, active=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.togglable = togglable
        self.active = active
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                if self.togglable:
                    self.active = not self.active
                self.callback(self.active)
                return True
        return False

    def draw(self, surface, font):
        if self.active:
            color = COLOR_BTN_ACTIVE_HOVER if self.hovered else COLOR_BTN_ACTIVE
        else:
            color = COLOR_BTN_HOVER if self.hovered else COLOR_BTN_BG
            
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 1, border_radius=5)
        
        text_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class entropyVisualizer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TrueEntropy Visualization Playground")
        self.clock = pygame.time.Clock()
        self.font_sml = pygame.font.SysFont("Consolas", 12)
        self.font_main = pygame.font.SysFont("Consolas", 15)
        self.font_large = pygame.font.SysFont("Consolas", 24)
        self.font_huge = pygame.font.SysFont("Consolas", 42)
        
        self.pool = EntropyPool()
        self.hybrid_tap = HybridTap(self.pool)
        self.collector = VisualizationCollector(self.pool)
        self.collector.start()
        
        self.running = True
        self.entropy_history: List[int] = []
        self.random_stream: List[str] = []
        
        # Histrogram data
        self.byte_history: List[int] = []
        self.MAX_BYTE_HISTORY = 2000
        
        # Health Data
        self.health_data = {}
        self.last_health_check = 0.0
        
        # Display state
        self.display_bits = 0.0 # For smooth animation
        self.constant_mode = False
        self.use_hybrid = False
        
        # Setup GUI Elements
        self.buttons = []
        self._setup_gui()
        
        logger.info("Visualizer initialized with GUI")

    def _setup_gui(self):
        y_start = 550
        x_col1 = 50
        x_col2 = 250
        
        # Mode Toggles
        self.buttons.append(Button((x_col1, y_start, 180, 35), "Hybrid Mode (Fast)", 
                                   lambda v: setattr(self, 'use_hybrid', v)))
        
        self.buttons.append(Button((x_col1, y_start + 45, 180, 35), "Offline Mode", 
                                   lambda v: self.collector.set_offline_mode(v)))
        
        self.buttons.append(Button((x_col1, y_start + 90, 180, 35), "Constant Drain", 
                                   lambda v: setattr(self, 'constant_mode', v)))

        # Harvester Toggles
        y_h = y_start
        for name in self.collector.statuses.keys():
            # Capture name in lambda default arg
            btn = Button((x_col2, y_h, 150, 30), f"Toggle {name}", 
                         lambda v, n=name: self.collector.toggle_harvester(n), 
                         active=True)
            self.buttons.append(btn)
            y_h += 35

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            for btn in self.buttons:
                btn.handle_event(event)
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._extract_entropy(32)
                elif event.key == pygame.K_r:
                    self.pool.reseed()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_e]: # Manual drain
            if self.pool.entropy_bits > 8:
                 self._extract_entropy(4)

    def _extract_entropy(self, count: int):
        try:
            if self.use_hybrid:
                # Hybrid mode uses PRNG seeded by pool, much faster, consumes less pool entropy
                data = self.hybrid_tap.randbytes(count)
            else:
                # True random extracts directly from pool
                data = self.pool.extract(count)
                
            self._add_to_stream(data)
        except ValueError:
             # Pool empty
             pass

    def _add_to_stream(self, data: bytes):
        hex_str = data.hex()
        pairs = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
        self.random_stream.extend(pairs)
        if len(self.random_stream) > 400:
            self.random_stream = self.random_stream[-400:]
            
        # Add to histogram buffer
        for b in data:
            self.byte_history.append(b)
        while len(self.byte_history) > self.MAX_BYTE_HISTORY:
            self.byte_history.pop(0)
            
    def update(self):
        target_bits = self.pool.entropy_bits
        
        # Smooth animation (lerp)
        self.display_bits += (target_bits - self.display_bits) * 0.1
        
        self.entropy_history.append(target_bits)
        # Increase history to match graph width roughly
        if len(self.entropy_history) > 700:
            self.entropy_history.pop(0)
            
        # Constant drain logic
        if self.constant_mode:
            # Drain ~X bytes/sec
            if self.pool.entropy_bits > 8:
                self._extract_entropy(1)
                
        # Update Health Check (periodically)
        if time.time() - self.last_health_check > 1.0:
             self.health_data = entropy_health(self.pool)
             self.last_health_check = time.time()

    def draw_pool_gauge(self, center_x: int, center_y: int, radius: int):
        fill_ratio = min(self.display_bits / MAX_BITS, 1.0)
        
        # Background
        pygame.draw.circle(self.screen, COLOR_POOL_EMPTY, (center_x, center_y), radius)
        
        # Animated Fill (Arc)
        if fill_ratio > 0.01:
            points = [(center_x, center_y)]
            num_points = max(10, int(360 * fill_ratio / 5)) 
            start_angle = -math.pi / 2
            total_angle = 2 * math.pi * fill_ratio
            
            for i in range(num_points + 1):
                ang = start_angle + (total_angle * (i / num_points))
                px = center_x + math.cos(ang) * (radius - 5)
                py = center_y + math.sin(ang) * (radius - 5)
                points.append((px, py))
                
            pygame.draw.polygon(self.screen, COLOR_POOL_FILL, points)
            
        pygame.draw.circle(self.screen, (200, 200, 200), (center_x, center_y), radius, 2)

        # Labels
        # Show Current Entropy vs Capacity
        
        # Entropy Level
        lbl_level = self.font_main.render("Current Entropy:", True, COLOR_TEXT_DIM)
        val_level = self.font_large.render(f"{int(self.display_bits)} bits", True, COLOR_TEXT)
        
        # Capacity (Fixed)
        lbl_cap = self.font_sml.render("Pool Capacity:", True, COLOR_TEXT_DIM)
        val_cap = self.font_sml.render(f"{POOL_SIZE} bytes ({MAX_BITS} bits)", True, (150, 150, 150))

        # Centered text positioning
        cx = center_x
        cy = center_y + radius + 15
        
        self.screen.blit(lbl_level, (cx - lbl_level.get_width()//2, cy))
        self.screen.blit(val_level, (cx - val_level.get_width()//2, cy + 20))
        
        self.screen.blit(lbl_cap, (cx - lbl_cap.get_width()//2, cy + 55))
        self.screen.blit(val_cap, (cx - val_cap.get_width()//2, cy + 70))

    def draw_graph(self, x: int, y: int, width: int, height: int):
        # Draw background
        pygame.draw.rect(self.screen, (20, 25, 30), (x, y, width, height), border_radius=5)
        pygame.draw.rect(self.screen, (60, 70, 80), (x, y, width, height), 1, border_radius=5)
        
        title = self.font_sml.render("Entropy History (Auto-Zoom)", True, COLOR_TEXT_DIM)
        self.screen.blit(title, (x+5, y+5))

        if len(self.entropy_history) < 2:
            return

        # Dynamic Scaling / Auto-Zoom
        min_val = min(self.entropy_history)
        max_val = max(self.entropy_history)
        
        # Ensure a minimum range to avoid flat lines looking chaotic on tiny noise
        val_range = max_val - min_val
        if val_range < 50:
            mid = (min_val + max_val) / 2
            min_val = mid - 25
            max_val = mid + 25
            val_range = 50
            
        points = []
        max_h = len(self.entropy_history)
        
        for i, val in enumerate(self.entropy_history):
            # i runs 0 to len
            px = x + (i * ((width-10) / max_h)) if max_h > 0 else x
            
            # Normalize to relative range
            rel_val = (val - min_val) / val_range
            rel_val = max(0.0, min(1.0, rel_val)) # Clamp
            
            py = (y + height - 5) - (rel_val * (height-25))
            points.append((px, py))
            
        if len(points) > 1:
            pygame.draw.lines(self.screen, COLOR_POOL_FILL, False, points, 2)
            
        # Draw min/max info
        lbl_max = self.font_sml.render(f"Max: {int(max_val)}", True, (100, 150, 100))
        lbl_min = self.font_sml.render(f"Min: {int(min_val)}", True, (150, 100, 100))
        self.screen.blit(lbl_max, (x + width - 80, y + 5))
        self.screen.blit(lbl_min, (x + width - 80, y + height - 20))

    def draw_histogram(self, x: int, y: int, width: int, height: int):
        pygame.draw.rect(self.screen, (20, 25, 30), (x, y, width, height), border_radius=5)
        
        title = self.font_main.render("Distribution Histogram (Byte Values 0-255)", True, COLOR_ACCENT)
        self.screen.blit(title, (x, y - 25))
        
        if not self.byte_history:
            msg = self.font_main.render("Extract entropy to see distribution", True, COLOR_TEXT_DIM)
            self.screen.blit(msg, (x + width//2 - msg.get_width()//2, y + height//2))
            return

        # Calculate frequencies
        counts = [0] * 256
        for b in self.byte_history:
            counts[b] += 1
            
        max_count = max(counts) if counts else 1
        bar_w = width / 256.0
        
        for i, count in enumerate(counts):
            if count == 0: continue
            
            bar_h = (count / max_count) * (height - 10)
            
            px = x + i * bar_w
            py = y + height - bar_h - 5
            
            # Color coding: Green if close to average, Red if outlier
            avg = len(self.byte_history) / 256
            deviation = abs(count - avg) / (avg if avg > 0 else 1)
            
            if deviation > 0.5 and len(self.byte_history) > 500: # High deviation
                 col = COLOR_HIST_BAD
            elif deviation < 0.2:
                 col = COLOR_HIST_GOOD
            else:
                 col = COLOR_HIST_BAR
            
            pygame.draw.rect(self.screen, col, (px, py, max(1, bar_w), bar_h))

    def draw_harvesters(self, x: int, y: int):
        title = self.font_large.render("Harvesters", True, COLOR_ACCENT)
        self.screen.blit(title, (x, y))
        
        y_pos = y + 40
        with self.collector.lock:
            for name, status in self.collector.statuses.items():
                if status.status == "DISABLED":
                    col = COLOR_HARVESTER_INACTIVE
                elif status.status == "COLLECTING":
                    col = COLOR_HARVESTER_WAITING
                elif status.status == "SUCCESS":
                    if time.time() - status.last_run < 0.5:
                        col = (200, 255, 200) 
                    else:
                        col = COLOR_HARVESTER_ACTIVE
                elif status.status == "ERROR":
                    col = COLOR_HARVESTER_ERROR
                else:
                    col = COLOR_HARVESTER_INACTIVE
                
                pygame.draw.circle(self.screen, col, (x + 10, y_pos + 10), 8)
                
                info = f"{name}"
                if status.status == "SUCCESS": 
                     info += f": +{status.last_bits}"
                elif status.status == "ERROR":
                    info += " !"
                elif status.status == "DISABLED":
                    info += " (OFF)"
                
                text = self.font_main.render(info, True, COLOR_TEXT if status.enabled else COLOR_TEXT_DIM)
                self.screen.blit(text, (x + 30, y_pos))
                y_pos += 30

    def draw_stream(self, x: int, y: int, width: int, height: int):
        pygame.draw.rect(self.screen, (20, 25, 30), (x, y, width, height), border_radius=5)
        
        title = self.font_main.render("Entropy Output Stream", True, COLOR_ACCENT)
        mode_txt = "Hybrid Mode" if self.use_hybrid else "True Random"
        sub_title = self.font_sml.render(mode_txt, True, (100, 200, 255) if self.use_hybrid else (200, 100, 255))
        
        self.screen.blit(title, (x, y - 25))
        self.screen.blit(sub_title, (x + width - sub_title.get_width(), y - 25))
        
        cols = width // 22
        rows = height // 18
        
        count = 0
        for i, val in enumerate(reversed(self.random_stream)):
            if count >= cols * rows: break
            
            c_col = count % cols
            c_row = count // cols
            
            px = x + 5 + c_col * 22
            py = y + 5 + c_row * 18
            
            # Color cycle
            v_int = int(val, 16)
            color = (v_int, 200, 255 - v_int)
            
            text = self.font_main.render(val, True, color)
            self.screen.blit(text, (px, py))
            count += 1
            
    def draw_health(self, x: int, y: int, width: int, height: int):
        # Background
        pygame.draw.rect(self.screen, (20, 25, 30), (x, y, width, height), border_radius=5)
        
        if not self.health_data:
            return
            
        score = self.health_data.get("score", 0)
        status = self.health_data.get("status", "unknown")
        
        # Color based on Status/Score
        if score >= 80: col = COLOR_HEALTH_OK
        elif score >= 50: col = COLOR_HEALTH_WARN
        else: col = COLOR_HEALTH_CRIT
        
        # Draw Score Big
        lbl_score = self.font_main.render("Health Score", True, COLOR_TEXT_DIM)
        val_score = self.font_huge.render(f"{score}", True, col)
        
        self.screen.blit(lbl_score, (x + 20, y + 15))
        self.screen.blit(val_score, (x + 20, y + 35))
        
        # Draw Status Status
        lbl_status = self.font_main.render(f"Status: {status.upper()}", True, col)
        self.screen.blit(lbl_status, (x + 140, y + 35))
        
        # Recommendation text
        rec = self.health_data.get("recommendation", "")
        if rec:
            lbl_rec = self.font_sml.render(rec, True, COLOR_TEXT_DIM)
            self.screen.blit(lbl_rec, (x + 140, y + 60))

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        # Left Panel (Gauges & Buttons)
        self.draw_pool_gauge(150, 150, 80)
        self.draw_harvesters(50, 360)
        
        for btn in self.buttons:
            btn.draw(self.screen, self.font_main)

        # Right Panel
        # Top: Health
        self.draw_health(450, 20, 700, 90)
        
        # Middle: Graphs & Stream (Increased Spacing to fix overlap)
        self.draw_graph(450, 140, 700, 150)
        
        # Stream starts further down
        self.draw_stream(450, 320, 700, 200)
        
        # Bottom Full Width (Histogram)
        # Histogram starts further down
        self.draw_histogram(450, 560, 700, 250)
        
        # FPS and Footer
        fps_text = self.font_sml.render(f"FPS: {int(self.clock.get_fps())}", True, COLOR_TEXT_DIM)
        self.screen.blit(fps_text, (10, WINDOW_HEIGHT - 20))
        
        help_text = self.font_main.render("SPACE: Extract | E: Drain | R: Reseed", True, COLOR_TEXT_DIM)
        self.screen.blit(help_text, (WINDOW_WIDTH - help_text.get_width() - 10, WINDOW_HEIGHT - 25))
        
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                self.handle_input()
                self.update()
                self.draw()
                self.clock.tick(FPS)
        except Exception as e:
            logger.critical(f"Crash: {e}", exc_info=True)
            raise e
        finally:
            self.collector.stop()
            pygame.quit()

if __name__ == "__main__":
    app = entropyVisualizer()
    app.run()
