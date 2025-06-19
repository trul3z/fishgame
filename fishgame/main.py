import tkinter as tk
from tkinter import messagebox 
import json
import random
import os
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
    print("✅ PIL/Pillow imported successfully")
except ImportError as e:
    print(f"❌ PIL/Pillow not available: {e}")
    print("💡 Install with: pip install Pillow")
    PIL_AVAILABLE = False
    Image = None
    ImageTk = None

class Fish:
    def __init__(self, fish_data):
        self.name = fish_data["name"]
        self.type = fish_data["type"]
        self.rarity = fish_data["rarity"]
        self.min_size = fish_data["min_size"]
        self.max_size = fish_data["max_size"]
        self.avg_size = fish_data["avg_size"]
        self.gold_value = fish_data["gold_value"]
        self.food_value = fish_data["food_value"]
        self.description = fish_data["description"]
        self.fish_effect = fish_data["fish_effect"]
    
        self.actual_size = round(random.uniform(self.min_size, self.max_size), 1)

    def get_sell_value(self):
        """Calculate gold value based on actual size vs average size with reduced impact"""
        if self.avg_size <= 0:
            return self.gold_value
        
        size_ratio = self.actual_size / self.avg_size
        
        if size_ratio >= 1.0:
            size_multiplier = 1.0 + min(0.25, (size_ratio - 1.0) * 0.5)
        else:
            size_multiplier = max(0.75, 1.0 - (1.0 - size_ratio) * 0.5)
        
        final_value = int(self.gold_value * size_multiplier)
        return max(1, final_value) 
    
    def __str__(self):
        return f"{self.name} (Rarity: {self.rarity}, Value: {self.gold_value}g)"

class Location:
    def __init__(self, location_data):
        self.name = location_data["name"]
        self.description = location_data["description"]
        self.fish_types = location_data["fish types"]
        self.item_types = location_data["item types"]
        self.enemy_types = location_data["enemy types"]
        self.fish_spawn_chance = location_data["fish spawn chance"]
        self.item_spawn_chance = location_data["item spawn chance"]
        self.gear_spawn_chance = location_data["gear spawn chance"]
        self.enemy_spawn_chance = location_data["enemy spawn chance"]
        self.catch_nothing_chance = location_data["catch nothing chance"]
        self.fishing_license_required = location_data["fishing license required"]
        self.unlocked_by_default = location_data["Unlocked by default"]
        self.unlock_condition = location_data["unlock condition"]
    
    def is_unlocked(self, player_trades_completed):
        """Check if this location is available to the player"""
        if self.unlocked_by_default:
            return True
        
        if self.unlock_condition == "Trade deck":
            # Check if this specific location has been unlocked
            location_key = f"unlocked_{self.name.lower().replace(' ', '_')}"
            return location_key in player_trades_completed
        
        return False
    
    def __str__(self):
        return f"{self.name} - Fish: {', '.join(self.fish_types)} (Fish chance: {self.fish_spawn_chance})"

class Item:
    def __init__(self, item_data):
        self.name = item_data["name"]
        self.rarity = item_data["rarity"]
        self.value = item_data["gold_value"]
        self.description = item_data["description"]
        self.item_type = item_data["item_type"]
        self.effect = item_data["effect"]
        self.quantity = item_data["quantity"] 

    def __str__(self):
        return f"{self.name} (Type: {self.item_type}, Value: {self.value}g, World qty: {self.quantity})"

class Gear:
    def __init__(self, gear_data):
        self.name = gear_data["name"]
        self.gear_type = gear_data["gear_type"] 
        self.gold_value = gear_data["gold_value"]
        self.rarity = gear_data.get("rarity", 1)  # Some items don't have rarity specified
        self.description = gear_data["description"]
        self.stat_bonus = gear_data.get("stat_bonus", {})  # attack, defense, speed, luck bonuses
        self.equipped = False  # Track if currently equipped by player
    
    def get_bonuses(self):
        """Return dictionary of stat bonuses this gear provides"""
        return self.stat_bonus
    
    def __str__(self):
        bonus_text = ""
        if self.stat_bonus:
            bonus_list = [f"+{value} {stat}" for stat, value in self.stat_bonus.items()]
            bonus_text = f" ({', '.join(bonus_list)})"
        return f"{self.name} [{self.gear_type}]{bonus_text} - {self.gold_value}g"

class Enemy:
    def __init__(self, enemy_data):
        self.name = enemy_data["name"]
        self.rarity = enemy_data["rarity"]
        self.health = enemy_data["health"]
        self.max_health = enemy_data["health"]  # Store original health for healing/reset
        self.attack = enemy_data["attack"]
        self.defense = enemy_data["defense"]
        self.speed = enemy_data["speed"]
        self.description = enemy_data["description"]
        self.attack_message = enemy_data.get("attack_message", f"{self.name} attacks!")
        self.loot_value = enemy_data["loot_value"]
        self.xp_reward = enemy_data["xp_reward"]
        self.enemy_type = enemy_data["enemy_type"]
    
    def is_alive(self):
        """Check if enemy is still alive"""
        return self.health > 0
    
    def take_damage(self, damage):
        """Take damage, reduced by defense"""
        actual_damage = max(1, damage - self.defense)  # Minimum 1 damage
        self.health -= actual_damage
        return actual_damage
    
    def __str__(self):
        return f"{self.name} (HP: {self.health}/{self.max_health}, ATK: {self.attack}, DEF: {self.defense})"

class Trade:
    def __init__(self, trade_data):
        self.name = trade_data["name"]
        self.trade_type = trade_data["type"]
        self.effect = trade_data["effect"]
        self.gold_value = trade_data["gold_value"]
        self.trigger = trade_data["trigger"]  # Can be a single dict or list of dicts
  
    def execute_trigger(self, player, game):
        """Execute the trigger action(s) based on structured trigger data"""
        results = []
        
        # Handle both single trigger and multiple triggers
        triggers = self.trigger if isinstance(self.trigger, list) else [self.trigger]
        
        for trigger in triggers:
            action = trigger["action"]
            target = trigger["target"]
            
            if action == "add_gear":
                # Find gear in gear.json and add to player inventory
                for gear_data in game.gear_data['gear']:
                    if gear_data['name'] == target:
                        gear = Gear(gear_data)
                        player.add_gear(gear)
                        results.append(f"{target} added to inventory!")
                        break
                else:
                    results.append(f"Gear '{target}' not found!")
            
            elif action == "add_item":
                # Find item in items.json and add to player inventory
                for item_data in game.item_data['items']:
                    if item_data['name'] == target:
                        item = Item(item_data)
                        player.add_item(item)
                        results.append(f"{target} added to inventory!")
                        break
                else:
                    results.append(f"Item '{target}' not found!")
            
            elif action == "increase_stat":
                # Increase player stat by specified amount
                amount = trigger.get("amount", 1)
                if target == "luck":
                    player.base_luck += amount
                    results.append(f"Luck increased by {amount}!")
                elif target == "attack":
                    player.base_attack += amount
                    results.append(f"Attack increased by {amount}!")
                elif target == "defense":
                    player.base_defense += amount
                    results.append(f"Defense increased by {amount}!")
                elif target == "speed":
                    player.base_speed += amount
                    results.append(f"Speed increased by {amount}!")
                elif target == "health":
                    player.max_health += amount
                    player.health += amount
                    results.append(f"Max health increased by {amount}!")
                else:
                    results.append(f"Unknown stat: {target}")
            
            elif action == "unlock_location":
                # NEW: Handle random location unlocking for "Venture Out" trade
                if self.name == "Venture Out":
                    # Find all locked locations that can be unlocked by trade deck
                    available_to_unlock = []
                    for loc_data in game.location_data['locations']:
                        location = Location(loc_data)
                        if (not location.unlocked_by_default and 
                            location.unlock_condition == "Trade deck" and 
                            not location.is_unlocked(player.completed_trades)):
                            available_to_unlock.append(location.name)
                    
                    if available_to_unlock:
                        # Pick ONE random location to unlock
                        import random
                        unlocked_location = random.choice(available_to_unlock)
                        
                        # Add a specific unlock key for this location
                        unlock_key = f"unlocked_{unlocked_location.lower().replace(' ', '_')}"
                        player.completed_trades.append(unlock_key)
                        
                        results.append(f"New fishing location unlocked: {unlocked_location}!")
                    else:
                        results.append("No new locations to unlock!")
                else:
                    # Legacy behavior for other trades
                    player.completed_trades.append(self.name)
                    results.append("New fishing location unlocked!")
            
            elif action == "unlock_license":
                # NEW: Handle fishing license unlocking
                if target == "fishing_license":
                    # Add fishing license to player
                    if not hasattr(player, 'has_fishing_license'):
                        player.has_fishing_license = False
                    
                    if player.has_fishing_license:
                        results.append("You already have a fishing license!")
                    else:
                        player.has_fishing_license = True
                        results.append("🎫 Fishing License obtained! You can now fish at licensed locations!")
                else:
                    results.append(f"Unknown license type: {target}")

            elif action == "heal":
                # Heal player by amount or percentage
                amount = trigger.get("amount", 50)
                player.health = min(player.max_health, player.health + amount)
                results.append(f"Healed for {amount} HP!")
            
            elif action == "add_gold":
                # Give player gold
                amount = trigger.get("amount", 100)
                player.gold += amount
                results.append(f"Gained {amount} gold!")
            
            else:
                results.append(f"Unknown action: {action}")
        
        return " ".join(results)
    
    def __str__(self):
        return f"{self.name} - {self.gold_value}g\nEffect: {self.effect}"

class Player:
    def __init__(self):
        # Basic stats
        self.health = 20
        self.max_health = 20
        self.gold = 0  
        self.energy = 15 
        self.max_energy = 100000000
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 20  # XP needed to level up
        
        # Base stats (before equipment bonuses)
        self.base_luck = 10
        self.base_attack = 10
        self.base_defense = 10
        self.base_speed = 10

        self.name = ""
        self.backstory = ""

        # Inventory
        self.inventory = []  
        self.gear_inventory = [] 
        self.completed_trades = []  
        self.trade_usage = {}  # ADD THIS LINE - tracks how many times each trade was used
        self.unlocked_locations = []  # Track unlocked locations by name
        self.completed_explorations = []  # Track completed explorations by name

        self.has_fishing_license = False  # Track if player has a fishing license
        
        # Equipment slots
        self.equipped_rod = None
        self.equipped_head = None
        self.equipped_torso = None
        self.equipped_leg = None
        self.equipped_foot = None
        self.equipped_glove = None
        self.equipped_necklace = None
        self.equipped_ring = None
        self.equipped_knife = None

        self.bait_boost_remaining = 0 
        self.exploration_counts = {}  # Track exploration counts for each type

    def take_damage(self, damage):
        """Take damage, used in combat"""
        self.health -= damage
        if self.health < 0:
            self.health = 0
        return damage

    def heal(self, amount):
        """Heal the player"""
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        actual_healing = self.health - old_health
        return actual_healing

    def is_alive(self):
        """Check if player is alive"""
        return self.health > 0

    def can_fish(self):
        return self.energy > 0
    
    def use_energy(self, amount=1):
        """Use energy for fishing or other actions"""
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def add_xp(self, amount):
        """Add XP and check for level up"""
        self.xp += amount
        
        # Check for level up
        if self.xp >= self.xp_to_next_level:
            return self.level_up()
        
        return None
    
    def level_up(self):
        """Handle level up - return True if leveled up"""
        if self.xp >= self.xp_to_next_level:
            self.level += 1
            self.xp -= self.xp_to_next_level
            
            # Increase XP requirement for next level (scales with level)
            self.xp_to_next_level = int(self.xp_to_next_level * 1.2)  # 20% increase each level
            
            # Heal player on level up
            old_health = self.health
            self.health = min(self.max_health, self.health + 5)  # Heal 5 HP on level up
            healing = self.health - old_health
            
            return f"🎉 LEVEL UP! Now level {self.level}! (+{healing} HP restored)"
        
        return None
    
    def get_xp_progress(self):
        """Get XP progress as percentage"""
        if self.xp_to_next_level <= 0:
            return 100
        return min(100, (self.xp / self.xp_to_next_level) * 100)
    
    def get_xp_display(self):
        """Get XP display string"""
        return f"{self.xp}/{self.xp_to_next_level} XP"

    def is_game_over(self):
        """Check if game is over (energy reaches 0)"""
        return self.energy <= 0

    def add_fish(self, fish):
        """Add caught fish to inventory"""
        self.inventory.append(fish)

    def get_fish_bonuses(self):
        """Calculate stat bonuses from fish in inventory"""
        fish_bonuses = {
            "luck": 0,
            "attack": 0,
            "defense": 0,
            "speed": 0
        }
        
        for item in self.inventory:
            if hasattr(item, 'fish_effect') and item.fish_effect != "none":
                # Parse fish effects from JSON
                effect = item.fish_effect.lower()
                
                # Extract number and stat from effect string
                import re
                
                # Match patterns like "+1 defense when held", "+3 luck when held", etc.
                match = re.search(r'\+(\d+)\s+(defense|attack|luck|speed)', effect)
                if match:
                    bonus_amount = int(match.group(1))
                    stat_type = match.group(2)
                    
                    if stat_type in fish_bonuses:
                        fish_bonuses[stat_type] += bonus_amount
        
        return fish_bonuses

    def add_item(self, item):
        """Add item to inventory"""
        self.inventory.append(item)
    
    def add_gear(self, gear):
        """Add gear to inventory"""
        self.gear_inventory.append(gear)
    
    def equip_gear(self, gear):
        """Equip gear to appropriate slot"""
        # Unequip current gear in that slot
        if gear.gear_type == "rod":
            if self.equipped_rod:
                self.equipped_rod.equipped = False
            self.equipped_rod = gear
        elif gear.gear_type == "head":
            if self.equipped_head:
                self.equipped_head.equipped = False
            self.equipped_head = gear
        elif gear.gear_type == "torso":
            if self.equipped_torso:
                self.equipped_torso.equipped = False
            self.equipped_torso = gear
        elif gear.gear_type == "leg":
            if self.equipped_leg:
                self.equipped_leg.equipped = False
            self.equipped_leg = gear
        elif gear.gear_type == "foot":
            if self.equipped_foot:
                self.equipped_foot.equipped = False
            self.equipped_foot = gear
        elif gear.gear_type == "glove":
            if self.equipped_glove:
                self.equipped_glove.equipped = False
            self.equipped_glove = gear
        elif gear.gear_type == "necklace":
            if self.equipped_necklace:
                self.equipped_necklace.equipped = False
            self.equipped_necklace = gear
        elif gear.gear_type == "ring":
            if self.equipped_ring:
                self.equipped_ring.equipped = False
            self.equipped_ring = gear
        elif gear.gear_type == "knife":
            if self.equipped_knife:
                self.equipped_knife.equipped = False
            self.equipped_knife = gear
        
        gear.equipped = True

    def can_purchase_trade(self, trade_name, trade_data):
        """Check if player can still purchase this trade"""
        used_count = self.trade_usage.get(trade_name, 0)
        max_quantity = trade_data.get("quantity", 1)
        return (max_quantity - used_count) > 0
    
    def get_remaining_trades(self, trade_name, trade_data):
        """Get how many times this trade can still be purchased"""
        used_count = self.trade_usage.get(trade_name, 0)
        max_quantity = trade_data.get("quantity", 1)
        return max(0, max_quantity - used_count)
    
    def use_trade(self, trade_name):
        """Record that this trade was purchased"""
        if trade_name not in self.trade_usage:
            self.trade_usage[trade_name] = 0
        self.trade_usage[trade_name] += 1

    def sell_fish(self, fish):
        """Sell a fish for gold"""
        if fish in self.inventory:
            gold_earned = fish.get_sell_value()
            self.gold += gold_earned
            self.inventory.remove(fish)
            return f"💰 Sold {fish.name} for {gold_earned} gold!"
        return "Fish not found in inventory!"
    
    def sell_item(self, item):
        """Sell an item for gold"""
        if item in self.inventory:
            gold_earned = item.value
            self.gold += gold_earned
            self.inventory.remove(item)
            return f"💰 Sold {item.name} for {gold_earned} gold!"
        return "Item not found in inventory!"

    def sell_gear(self, gear):
        """Sell gear for gold"""
        if gear in self.gear_inventory:
            gold_earned = gear.gold_value
            self.gold += gold_earned
            self.gear_inventory.remove(gear)
            return f"💰 Sold {gear.name} for {gear.gold_value} gold!"
        return "Gear not found in inventory!"
    
    def get_sellable_items(self):
        """Get all items that can be sold"""
        sellable = []
        
        # Add fish from inventory
        for fish in self.inventory:
            if hasattr(fish, 'get_sell_value'):  # Check if it's a fish
                sellable.append(('fish', fish, f"{fish.name} - {fish.get_sell_value()}g"))
        
        # Add items from inventory
        for item in self.inventory:
            if hasattr(item, 'value') and not hasattr(item, 'get_sell_value'):  # Check if it's an item, not fish
                sellable.append(('item', item, f"{item.name} - {item.value}g"))
        
        # Add gear from gear inventory
        for gear in self.gear_inventory:
            if not gear.equipped:  # Can't sell equipped gear
                sellable.append(('gear', gear, f"{gear.name} - {gear.gold_value}g"))

        return sellable

    def get_total_stats(self):
        """Calculate total stats including equipment bonuses"""
        # Add safety check at the beginning
        if not hasattr(self, 'base_luck'):
            self.base_luck = 0
        if not hasattr(self, 'base_attack'):
            self.base_attack = 10
        if not hasattr(self, 'base_defense'):
            self.base_defense = 10
        if not hasattr(self, 'base_speed'):
            self.base_speed = 5
        
        total_luck = self.base_luck
        total_attack = self.base_attack
        total_defense = self.base_defense
        total_speed = self.base_speed
        
        # Add bonuses from all equipped gear
        equipped_items = [
            self.equipped_rod, self.equipped_head, self.equipped_torso,
            self.equipped_leg, self.equipped_foot, self.equipped_glove,
            self.equipped_necklace, self.equipped_ring, self.equipped_knife
        ]
        
        for gear in equipped_items:
            if gear and hasattr(gear, 'stat_bonus') and gear.stat_bonus:
                total_luck += gear.stat_bonus.get("luck", 0)
                total_attack += gear.stat_bonus.get("attack", 0)
                total_defense += gear.stat_bonus.get("defense", 0)
                total_speed += gear.stat_bonus.get("speed", 0)

        # Add bonuses from fish in inventory - with safety check
        try:
            fish_bonuses = self.get_fish_bonuses()
            total_luck += fish_bonuses.get("luck", 0)
            total_attack += fish_bonuses.get("attack", 0)
            total_defense += fish_bonuses.get("defense", 0)
            total_speed += fish_bonuses.get("speed", 0)
        except:
            # If get_fish_bonuses fails, just skip fish bonuses
            pass

        return {
            "luck": total_luck,
            "attack": total_attack,
            "defense": total_defense,
            "speed": total_speed
        }
    
    def eat_fish(self, fish):
        """Eat a fish to restore energy"""
        if fish in self.inventory:
            energy_restored = fish.food_value
            old_energy = self.energy
            self.energy = min(self.max_energy, self.energy + energy_restored)
            actual_energy_gained = self.energy - old_energy
            
            self.inventory.remove(fish)
            return f"🍽️ Ate {fish.name}! Restored {actual_energy_gained} energy (was at max: {old_energy == self.max_energy})"
        return "Fish not found in inventory!"

    def __str__(self):
        stats = self.get_total_stats()
        return f"Player - HP: {self.health}/{self.max_health}, Gold: {self.gold}, Luck: {stats['luck']}, Attack: {stats['attack']}, Defense: {stats['defense']}"

class FishingGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tyler and Koda's Fishing Game")
        self.root.geometry("1260x720")  
        self.root.resizable(True, True)
        self.root.configure(bg="#87CEEB")
        self.root.state('zoomed') 
        self.gif_running = False
     
        self.create_widgets()
        self.load_json_data()

        self.player_completed_explorations = []

    def create_widgets(self):
        # Try to load and display image/gif with better error handling
        try:
            # Get the directory where the script is located
            base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"🔍 Looking for images in: {base_dir}")
            
            # Try to load image - check for multiple possible image files
            possible_images = ["koda_fishing.gif", "main_image.gif", "fishing.gif", "game_logo.gif"]
            image_loaded = False
            
            for image_name in possible_images:
                image_path = os.path.join(base_dir, image_name)
                if os.path.exists(image_path):
                    print(f"✅ Found image: {image_name}")
                    try:
                        # Load the image/gif
                        self.logo_image = tk.PhotoImage(file=image_path)
                        
                        # Display the image
                        self.logo_label = tk.Label(self.root, image=self.logo_image, bg="#87CEEB")
                        self.logo_label.pack(pady=10)
                        
                        # If it's an animated GIF, start the animation
                        if image_path.lower().endswith('.gif'):
                            self.animate_gif()
                        
                        image_loaded = True
                        break
                    except Exception as img_error:
                        print(f"❌ Error loading {image_name}: {img_error}")
                        continue
            
            if not image_loaded:
                print("⚠️ No image files found, using text placeholder")
                # List what files are actually in the directory
                files_in_dir = [f for f in os.listdir(base_dir) if f.lower().endswith(('.gif', '.png', '.jpg', '.jpeg'))]
                if files_in_dir:
                    print(f"📁 Image files found in directory: {files_in_dir}")
                else:
                    print("📁 No image files found in directory")
                
                # If image loading fails, show a text placeholder
                self.logo_label = tk.Label(self.root, text="🎣", font=("Helvetica", 48), bg="#87CEEB")
                self.logo_label.pack(pady=10)
            
        except Exception as e:
            print(f"❌ General error in create_widgets: {e}")
            # If anything fails, show a text placeholder
            self.logo_label = tk.Label(self.root, text="🎣", font=("Helvetica", 48), bg="#87CEEB")
            self.logo_label.pack(pady=10)

        self.title_label = tk.Label(self.root, text="Tyler and Koda's Fishing Game", font=("Helvetica", 24), bg="#87CEEB")
        self.title_label.pack(pady=20)

        self.start_button = tk.Button(self.root, text="Start Game", font=("Helvetica", 18), command=self.start_game)
        self.start_button.pack(pady=10)

        self.quit_button = tk.Button(self.root, text="Quit", font=("Helvetica", 18), command=self.root.quit)
        self.quit_button.pack(pady=10)

    def animate_gif(self):
        """Animate GIF frames with automatic transitions and better error handling"""
        try:
            # Determine which GIF to load based on current state
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Default to koda_fishing.gif if no current_gif is set
            if not hasattr(self, 'current_gif'):
                self.current_gif = "koda_fishing"
            
            # Choose image path based on current GIF
            gif_files = {
                "start_adventure": "start_adventure.gif",
                "village_pond_enter": "village_pond_enter.gif", 
                "village_pond_cast": "village_pond_cast.gif",
                "village_pond": "village_pond.gif",
                "koda_fishing": "koda_fishing.gif"
            }
            
            gif_filename = gif_files.get(self.current_gif, "koda_fishing.gif")
            image_path = os.path.join(base_dir, gif_filename)
            
            # Check if the specific GIF exists, fallback to any available GIF
            if not os.path.exists(image_path):
                print(f"⚠️ {gif_filename} not found, looking for alternatives...")
                
                # Try to find any GIF file
                available_gifs = [f for f in os.listdir(base_dir) if f.lower().endswith('.gif')]
                if available_gifs:
                    image_path = os.path.join(base_dir, available_gifs[0])
                    print(f"✅ Using alternative: {available_gifs[0]}")
                else:
                    print("❌ No GIF files found for animation")
                    return
            
            if not hasattr(self, 'gif_frames') or not self.gif_frames:
                # Load all frames of the current GIF
                self.gif_frames = []
                self.current_frame = 0
                
                # Try to load multiple frames
                frame_index = 0
                while True:
                    try:
                        frame = tk.PhotoImage(file=image_path, format=f"gif -index {frame_index}")
                        scaled_frame = frame.zoom(5)  # Reduced size for more space
                        self.gif_frames.append(scaled_frame)
                        frame_index += 1
                    except:
                        break
                
                if not self.gif_frames:
                    print(f"❌ No frames loaded from {gif_filename}")
                    return
            
            # If we have multiple frames, animate them
            if len(self.gif_frames) > 1:
                # Update the image
                if hasattr(self, 'logo_label'):
                    self.logo_label.config(image=self.gif_frames[self.current_frame])
                
                # Move to next frame
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                
                # Handle transitions based on current GIF and frame completion
                if self.current_frame == 0:  # Just completed a full loop
                    
                    # FIXED: start_adventure.gif plays once then goes to village_pond_enter.gif
                    if (hasattr(self, 'current_gif') and 
                        self.current_gif == "start_adventure"):
                        
                        if not hasattr(self, 'start_adventure_cycles'):
                            self.start_adventure_cycles = 0
                        
                        self.start_adventure_cycles += 1
                        
                        if self.start_adventure_cycles >= 1:  # Play once
                            print("🎬 Start adventure GIF completed, switching to village pond enter...")
                            self.switch_to_village_pond_enter_gif()
                            return
                    
                    # FIXED: village_pond_enter.gif plays once then goes to village_pond.gif
                    elif (hasattr(self, 'current_gif') and 
                        self.current_gif == "village_pond_enter"):
                        
                        if not hasattr(self, 'village_pond_enter_cycles'):
                            self.village_pond_enter_cycles = 0
                        
                        self.village_pond_enter_cycles += 1
                        
                        if self.village_pond_enter_cycles >= 1:  # Play once
                            print("🎬 Village pond enter GIF completed, switching to village pond...")
                            self.switch_to_village_pond_gif()
                            # FIXED: Don't return here - let the animation continue
                            # The switch_to_village_pond_gif() will reset frames and continue
                    
                    # FIXED: village_pond_cast.gif plays once then goes back to village_pond.gif
                    elif (hasattr(self, 'current_gif') and 
                        self.current_gif == "village_pond_cast"):
                        
                        if not hasattr(self, 'village_pond_cast_cycles'):
                            self.village_pond_cast_cycles = 0
                        
                        self.village_pond_cast_cycles += 1
                        
                        if self.village_pond_cast_cycles >= 1:  # Play once
                            print("🎬 Village pond cast GIF completed, switching back to village pond...")
                            self.switch_to_village_pond_gif()
                            # FIXED: Don't return here - let the animation continue
                            # The switch_to_village_pond_gif() will reset frames and continue
                    
                    # FIXED: Add explicit handling for village_pond and koda_fishing to loop infinitely
                    elif (hasattr(self, 'current_gif') and 
                        self.current_gif == "village_pond"):
                        # Just continue looping - no return statement, no actions
                        pass
                    
                    elif (hasattr(self, 'current_gif') and 
                        self.current_gif == "koda_fishing"):
                        pass
            
            # Schedule next frame update (this happens for ALL GIFs now - moved outside the transitions)
            self.root.after(100, self.animate_gif)
            
        except Exception as e:
            print(f"❌ GIF animation error: {e}")
            return

    def switch_to_start_adventure_gif(self):
        """Switch the main GIF to start_adventure.gif"""
        self.switch_gif("start_adventure")

    def switch_to_village_pond_enter_gif(self):
        """Switch the main GIF to village_pond_enter.gif"""
        self.switch_gif("village_pond_enter")

    def switch_to_village_pond_gif(self):
        """Switch the main GIF to village_pond.gif"""
        self.switch_gif("village_pond")

    def switch_to_village_pond_cast_gif(self):
        """Switch the main GIF to village_pond_cast.gif for one loop, then back to village_pond.gif"""
        self.switch_gif("village_pond_cast")

    def switch_gif(self, gif_key):
        """Generic method to switch to any GIF"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Map gif keys to filenames
            gif_files = {
                "start_adventure": "start_adventure.gif",
                "village_pond_enter": "village_pond_enter.gif", 
                "village_pond_cast": "village_pond_cast.gif",
                "village_pond": "village_pond.gif",
                "koda_fishing": "koda_fishing.gif"
            }
            
            gif_filename = gif_files.get(gif_key, "koda_fishing.gif")
            new_image_path = os.path.join(base_dir, gif_filename)
            
            if os.path.exists(new_image_path):
                # Reset GIF animation variables to force reload
                self.gif_frames = []
                self.current_frame = 0
                
                # Set the current gif flag
                self.current_gif = gif_key
                
                # Reset cycle counters for transition GIFs
                if gif_key == "start_adventure":
                    self.start_adventure_cycles = 0
                elif gif_key == "village_pond_enter":
                    self.village_pond_enter_cycles = 0
                elif gif_key == "village_pond_cast":
                    self.village_pond_cast_cycles = 0
                
                print(f"✅ Switched to {gif_filename}")
                
                # Force immediate reload in animate_gif by clearing frames
                # The next call to animate_gif will reload the frames with zoom applied
                
            else:
                print(f"❌ {gif_filename} not found")
                
        except Exception as e:
            print(f"Error switching GIF: {e}")

    def load_json_data(self):
        """Load all the JSON files from the script's directory"""
        try:
            # Get the directory where the script is located
            base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"🔍 Loading files from: {base_dir}")

            # Try to load each JSON file
            json_files = ["fish.json", "items.json", "gear.json", "enemies.json", "locations.json", "trade.json"]
            
            for json_file in json_files:
                file_path = os.path.join(base_dir, json_file)
                if not os.path.exists(file_path):
                    print(f"❌ Missing file: {json_file}")
                    print(f"   Expected at: {file_path}")
                else:
                    print(f"✅ Found: {json_file}")

            with open(os.path.join(base_dir, "fish.json"), "r") as f:
                self.fish_data = json.load(f)
            print("✅ Fish data loaded successfully")

            with open(os.path.join(base_dir, "items.json"), "r") as f:
                self.item_data = json.load(f)
            print("✅ Item data loaded successfully")

            with open(os.path.join(base_dir, "gear.json"), "r") as f:
                self.gear_data = json.load(f)
            print("✅ Gear data loaded successfully")
            
            with open(os.path.join(base_dir, "enemies.json"), "r") as f:
                self.enemy_data = json.load(f)
            print("✅ Enemy data loaded successfully")
            
            with open(os.path.join(base_dir, "locations.json"), "r") as f:
                self.location_data = json.load(f)
            print("✅ Location data loaded successfully")
            
            with open(os.path.join(base_dir, "trade.json"), "r") as f:
                self.trade_data = json.load(f)
            print("✅ Trade data loaded successfully")
            
            # FIXED: Add encoding='utf-8' to handle Unicode characters
            try:
                with open(os.path.join(base_dir, 'exploration.json'), 'r', encoding='utf-8') as f:
                    self.exploration_data = json.load(f)
                print("✅ Exploration data loaded successfully")
            except FileNotFoundError:
                print("⚠️ exploration.json not found - exploration events disabled")
                self.exploration_data = {"explorations": {}}
            except UnicodeDecodeError as e:
                print(f"❌ Unicode error reading exploration.json: {e}")
                print("💡 Try resaving exploration.json with UTF-8 encoding")
                self.exploration_data = {"explorations": {}}
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error in exploration.json: {e}")
                self.exploration_data = {"explorations": {}}
           
            print(f"Total loaded: {len(self.fish_data['fish'])} fish, {len(self.item_data['items'])} items, {len(self.gear_data['gear'])} gear, {len(self.enemy_data['enemies'])} enemies, {len(self.location_data['locations'])} locations, {len(self.trade_data['trade'])} trade options")

            # ADD THIS NEW METHOD CALL HERE
            self.create_location_enemy_mapping()

        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            self.fish_data = {'fish': []}
            self.item_data = {'items': []}
            self.gear_data = {'gear': []}
            self.enemy_data = {'enemies': []}
            self.location_data = {'locations': []}
            self.trade_data = {'trade': []}

    def go_fishing(self, location_name):
        """Go fishing at a location - can catch fish, items, gear, encounter enemies, or catch nothing"""
        if not hasattr(self, 'player') or self.player is None:
            return "No player found! Please start a new game first."

        # Find location
        location = None
        for loc_data in self.location_data['locations']:
            if loc_data['name'] == location_name:
                location = Location(loc_data)
                break

        if not location:
            return "Location not found!"

        # Get player luck for calculations
        player_luck = self.player.get_total_stats()['luck'] if hasattr(self, 'player') and self.player else 0

        # CHECK FOR BAIT BOOST AND APPLY TO SPAWN CHANCES
        bait_multiplier = 1.0
        bait_active_msg = ""
        
        # Initialize bait boost if it doesn't exist
        if not hasattr(self.player, 'bait_boost_remaining'):
            self.player.bait_boost_remaining = 0
        
        # FIXED: Check bait_boost_remaining instead of bait_boost_active
        if self.player.bait_boost_remaining > 0:
            bait_multiplier = 1.3  # 30% better catch rates
            self.player.bait_boost_remaining -= 1
            remaining = self.player.bait_boost_remaining
            # This message will be returned along with the catch result
            bait_active_msg = f" 🎣 Bait boost active! ({remaining} uses remaining)"

        # Apply bait boost to location spawn chances
        boosted_fish_chance = location.fish_spawn_chance * bait_multiplier
        boosted_item_chance = location.item_spawn_chance * bait_multiplier  
        boosted_gear_chance = location.gear_spawn_chance * bait_multiplier
        # Don't boost enemy chance - bait shouldn't attract more enemies!        

        # Stage 1: What happens when you cast your line? (cumulative probability)
        rand = random.random()
        cumulative = 0

        cumulative += boosted_fish_chance
        if rand < cumulative:
            result = self.catch_fish(location)
            return (result or "🎣 Something happened while fishing...") + bait_active_msg

        cumulative += boosted_item_chance
        if rand < cumulative:
            result = self.catch_item(location)
            return (result or "📦 Something happened while finding items...") + bait_active_msg

        cumulative += boosted_gear_chance
        if rand < cumulative:
            result = self.catch_gear(location)
            return (result or "⚔️ Something happened while finding gear...") + bait_active_msg

        cumulative += location.enemy_spawn_chance
        if rand < cumulative:
            # FIXED: Use location-specific enemies
            location_obj = None
            for loc_data in self.location_data['locations']:
                if loc_data['name'] == location_name:
                    location_obj = Location(loc_data)
                    break
            
            if location_obj:
                return self.encounter_enemy(location_obj) + bait_active_msg
            else:
                return "🦈 Enemy encountered but location error!" + bait_active_msg

        # Apply luck reduction to "nothing" chance (1% per luck point, max 15% reduction)
        luck_nothing_reduction = min(0.15, player_luck * 0.01)
        adjusted_nothing_chance = max(0.05, location.catch_nothing_chance - luck_nothing_reduction)

        cumulative += adjusted_nothing_chance
        if rand < cumulative:
            return "🎣 Nothing caught... try again!" + bait_active_msg

        # Catch nothing (remaining probability)
        return "🎣 Nothing caught... try again!" + bait_active_msg

    def create_location_enemy_mapping(self):
        """Create mapping of location names to their enemy types"""
        self.location_enemy_types = {}
        for loc_data in self.location_data['locations']:
            location_name = loc_data['name']
            enemy_types = loc_data.get('enemy types', [])
            self.location_enemy_types[location_name] = enemy_types

    def encounter_enemy(self, location):
        """Encounter an enemy and start combat - FIXED to use location enemy types"""
        # Get valid enemies for this location
        valid_enemies = self.get_valid_enemies_for_location(location.name)
        
        if not valid_enemies:
            return f"🦈 Enemy encountered but none available for {location.name}!"
        
        # Weighted random selection by rarity (lower rarity = more common)
        weights = [max(1, 1000 - enemy.get('rarity', 1)) for enemy in valid_enemies]
        enemy_data = random.choices(valid_enemies, weights=weights)[0]
        enemy = Enemy(enemy_data)
        
        # Start combat
        combat_result = self.start_combat(enemy)
        return combat_result

    def get_valid_enemies_for_location(self, location_name):
        """Get enemies that can spawn at this location"""
        valid_enemies = []
        
        # Get enemy types allowed at this location
        allowed_enemy_types = self.location_enemy_types.get(location_name, [])
        
        if not allowed_enemy_types:
            return []  # No enemies if no types specified
        
        for enemy_data in self.enemy_data['enemies']:
            enemy_type = enemy_data.get('enemy_type', '')
            
            # Check if the enemy's type matches any of the location's allowed types
            if enemy_type in allowed_enemy_types:
                valid_enemies.append(enemy_data)
        
        return valid_enemies

    def start_combat(self, enemy):
        """Start combat with an enemy"""
        if not hasattr(self, 'player') or self.player is None:
            return "No player found!"
        
        # Create combat window
        self.combat_window = tk.Toplevel(self.root)
        self.combat_window.title(f"Combat: {enemy.name}")
        self.combat_window.geometry("1000x800")
        self.combat_window.configure(bg="#2C3E50")
        self.combat_window.resizable(False, False)
        
        # Make window modal
        self.combat_window.transient(self.root)
        self.combat_window.grab_set()
        
        # Store enemy for combat methods
        self.current_enemy = enemy
        self.combat_log = []
        self.player_turn = True
        
        # Combat title
        title_label = tk.Label(self.combat_window, text=f"⚔️ COMBAT: {enemy.name}", 
                              font=("Helvetica", 20, "bold"), bg="#2C3E50", fg="#E74C3C")
        title_label.pack(pady=10)
        
        # Main combat frame
        main_frame = tk.Frame(self.combat_window, bg="#2C3E50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Player info
        player_frame = tk.Frame(main_frame, bg="#3498DB", relief=tk.RAISED, bd=2)
        player_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(player_frame, text=f"👤 {self.player.name}", 
                font=("Helvetica", 16, "bold"), bg="#3498DB", fg="white").pack(pady=5)
        
        # Player stats
        player_stats = self.player.get_total_stats()
        self.player_health_label = tk.Label(player_frame, text=f"❤️ HP: {self.player.health}/{self.player.max_health}", 
                                           font=("Helvetica", 14), bg="#3498DB", fg="white")
        self.player_health_label.pack(pady=2)
        
        tk.Label(player_frame, text=f"⚔️ Attack: {player_stats['attack']}", 
                font=("Helvetica", 12), bg="#3498DB", fg="white").pack(pady=1)
        tk.Label(player_frame, text=f"🛡️ Defense: {player_stats['defense']}", 
                font=("Helvetica", 12), bg="#3498DB", fg="white").pack(pady=1)
        tk.Label(player_frame, text=f"💨 Speed: {player_stats['speed']}", 
                font=("Helvetica", 12), bg="#3498DB", fg="white").pack(pady=1)
        tk.Label(player_frame, text=f"🍀 Luck: {player_stats['luck']}", 
                font=("Helvetica", 12), bg="#3498DB", fg="white").pack(pady=1)
        
        # Right side - Enemy info
        enemy_frame = tk.Frame(main_frame, bg="#E74C3C", relief=tk.RAISED, bd=2)
        enemy_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(enemy_frame, text=f"👹 {enemy.name}", 
                font=("Helvetica", 16, "bold"), bg="#E74C3C", fg="white").pack(pady=5)
        
        self.enemy_health_label = tk.Label(enemy_frame, text=f"❤️ HP: {enemy.health}/{enemy.max_health}", 
                                          font=("Helvetica", 14), bg="#E74C3C", fg="white")
        self.enemy_health_label.pack(pady=2)
        
        tk.Label(enemy_frame, text=f"⚔️ Attack: {enemy.attack}", 
                font=("Helvetica", 12), bg="#E74C3C", fg="white").pack(pady=1)
        tk.Label(enemy_frame, text=f"🛡️ Defense: {enemy.defense}", 
                font=("Helvetica", 12), bg="#E74C3C", fg="white").pack(pady=1)
        tk.Label(enemy_frame, text=f"💨 Speed: {enemy.speed}", 
                font=("Helvetica", 12), bg="#E74C3C", fg="white").pack(pady=1)
        
        tk.Label(enemy_frame, text=enemy.description, 
                font=("Helvetica", 10), bg="#E74C3C", fg="white", 
                wraplength=200, justify=tk.CENTER).pack(pady=5)
        
        # Combat log
        log_frame = tk.Frame(self.combat_window, bg="#34495E", relief=tk.SUNKEN, bd=2)
        log_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(log_frame, text="Combat Log:", 
                font=("Helvetica", 12, "bold"), bg="#34495E", fg="white").pack(anchor=tk.W, padx=5)
        
        self.combat_log_text = tk.Text(log_frame, height=8, font=("Helvetica", 10), 
                                      bg="#2C3E50", fg="white", state=tk.DISABLED)
        self.combat_log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Action buttons
        button_frame = tk.Frame(self.combat_window, bg="#2C3E50")
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.attack_btn = tk.Button(button_frame, text="⚔️ Attack", 
                                   font=("Helvetica", 12, "bold"), bg="#E67E22", fg="white",
                                   command=self.player_attack, width=10)
        self.attack_btn.pack(side=tk.LEFT, padx=5)
        
        self.flee_btn = tk.Button(button_frame, text="🏃 Flee", 
                                 font=("Helvetica", 12, "bold"), bg="#95A5A6", fg="white",
                                 command=self.attempt_flee, width=10)
        self.flee_btn.pack(side=tk.LEFT, padx=5)
        
        # Initial combat message
        self.add_combat_log(f"🦈 A wild {enemy.name} appears!")
        self.add_combat_log(f"💪 Prepare for battle!")
        
        self.calculate_turn_order()

        return f"⚔️ Combat started with {enemy.name}!"

    def calculate_turn_order(self):
        """Calculate turn order with initiative rolls and multiple attacks"""
        if not hasattr(self, 'player') or self.player is None:
            return "No player found!"   
        
        player_stats = self.player.get_total_stats()
        
        # Initiative rolls (1d10 + speed)
        player_init_roll = random.randint(1, 10)
        enemy_init_roll = random.randint(1, 10)

        # Luck bonus to initiative (luck/2, rounded down)
        luck_bonus = player_stats['luck'] // 2
        
        player_initiative = player_init_roll + player_stats['speed'] + luck_bonus
        enemy_initiative = enemy_init_roll + self.current_enemy.speed
        
        self.add_combat_log(f"🎲 Initiative rolls:")
        self.add_combat_log(f"   You: {player_init_roll} + {player_stats['speed']} speed + {luck_bonus} luck = {player_initiative}")
        self.add_combat_log(f"   {self.current_enemy.name}: {enemy_init_roll} + {self.current_enemy.speed} speed = {enemy_initiative}")
        
        # Calculate actions per turn based on speed advantage
        player_speed = player_stats['speed']
        enemy_speed = self.current_enemy.speed
        
       # Base ratio calculation
        if enemy_speed > 0:  # Avoid division by zero
            speed_ratio = player_speed / enemy_speed
            enemy_ratio = enemy_speed / player_speed
        else:
            speed_ratio = player_speed
            enemy_ratio = 0.1
        
        # Calculate base attacks (minimum 1)
        base_player_attacks = max(1, round(speed_ratio))
        base_enemy_attacks = max(1, round(enemy_ratio))
        
        # Add some variance (±1 attack, but never below 1)
        variance = random.choice([-1, 0, 0, 1])  # More likely to get base amount
        
        self.player_attacks_per_turn = max(1, base_player_attacks + variance)
        self.enemy_attacks_per_turn = max(1, base_enemy_attacks + variance)
        
        # Cap maximum attacks to prevent crazy numbers
        self.player_attacks_per_turn = min(5, self.player_attacks_per_turn)
        self.enemy_attacks_per_turn = min(5, self.enemy_attacks_per_turn)
        
        # Log attack calculations
        self.add_combat_log(f"💨 Speed Analysis:")
        self.add_combat_log(f"   Speed Ratio: {speed_ratio:.1f}:1 (You:{player_speed} vs Enemy:{enemy_speed})")
        
        if self.player_attacks_per_turn > 1:
            self.add_combat_log(f"   💫 You get {self.player_attacks_per_turn} attacks per turn!")
        
        if self.enemy_attacks_per_turn > 1:
            self.add_combat_log(f"   💫 {self.current_enemy.name} gets {self.enemy_attacks_per_turn} attacks per turn!")
        
        # Determine who goes first
        if player_initiative >= enemy_initiative:
            self.add_combat_log(f"💨 You go first! (Initiative: {player_initiative} vs {enemy_initiative})")
            self.player_turn = True
            self.current_attack_count = 0
        else:
            self.add_combat_log(f"💨 {self.current_enemy.name} goes first! (Initiative: {enemy_initiative} vs {player_initiative})")
            self.player_turn = False
            self.current_attack_count = 0
            self.root.after(2000, self.enemy_turn)

    def add_combat_log(self, message):
        """Add message to combat log"""
        if hasattr(self, 'combat_log_text'):
            self.combat_log_text.config(state=tk.NORMAL)
            self.combat_log_text.insert(tk.END, f"{message}\n")
            self.combat_log_text.config(state=tk.DISABLED)
            self.combat_log_text.see(tk.END)

    def player_attack(self):
        """Player attacks the enemy"""
        if not self.player_turn:
            return
        
        if not hasattr(self, 'player') or self.player is None:
            return

        # DISABLE ATTACK AND FLEE BUTTONS IMMEDIATELY to prevent spam
        if hasattr(self, 'attack_btn'):
            self.attack_btn.config(state=tk.DISABLED)
        if hasattr(self, 'flee_btn'):
            self.flee_btn.config(state=tk.DISABLED)

        # Initialize attack count if not set
        if not hasattr(self, 'current_attack_count'):
            self.current_attack_count = 0
        
        player_stats = self.player.get_total_stats()
        
        # Calculate damage
        base_damage = player_stats['attack']
        
        # Check for critical hit (luck increases crit chance)
        crit_chance = 5 + (player_stats['luck'] * 1)  # Base 5% + 1% per luck point
        is_crit = random.randint(1, 100) <= crit_chance
        
        if is_crit:
            damage = int(base_damage * 1.5)  # 50% more damage on crit
            self.add_combat_log(f"🎯 CRITICAL HIT! You deal {damage} damage to {self.current_enemy.name}!")
        else:
            damage = base_damage
            self.add_combat_log(f"⚔️ You attack {self.current_enemy.name} for {damage} damage!")
        
        # Apply damage to enemy
        actual_damage = self.current_enemy.take_damage(damage)
        
        # Update enemy health display
        self.enemy_health_label.config(text=f"❤️ HP: {self.current_enemy.health}/{self.current_enemy.max_health}")
        
        # Check if enemy is defeated
        if self.current_enemy.health <= 0:
            self.combat_victory()
            return

        # Increment attack count
        self.current_attack_count += 1
        
        # Check if player has more attacks this turn
        if self.current_attack_count < self.player_attacks_per_turn:
            # Allow another attack with a short delay for readability
            if self.current_attack_count < self.player_attacks_per_turn - 1:
                self.add_combat_log(f"💫 Quick follow-up attack incoming...")
            self.root.after(800, lambda: self.player_attack() if self.player_turn else None)
            return

        # All attacks used, switch to enemy turn
        self.current_attack_count = 0
        self.player_turn = False
        self.attack_btn.config(state=tk.DISABLED)
        self.flee_btn.config(state=tk.DISABLED)        
        # Enemy attacks after delay
        self.root.after(1500, self.enemy_turn)

    def enemy_turn(self):
        """Enemy attacks the player with damage accumulation system"""
        if self.player_turn or not self.current_enemy.is_alive():
            return
        
        if not hasattr(self, 'player') or self.player is None:
            return

        # Initialize damage accumulation if not set
        if not hasattr(self, 'accumulated_damage'):
            self.accumulated_damage = 0
        
        # Initialize attack count if not set
        if not hasattr(self, 'current_attack_count'):
            self.current_attack_count = 0

        # Calculate enemy damage
        base_damage = self.current_enemy.attack
        player_stats = self.player.get_total_stats()
        player_defense = player_stats['defense']
        
        # Accumulate damage from this attack
        self.accumulated_damage += base_damage
        
        # Use the enemy's attack message if available, otherwise use default
        if hasattr(self.current_enemy, 'attack_message'):
            attack_msg = self.current_enemy.attack_message
        else:
            attack_msg = f"{self.current_enemy.name} attacks you!"
        
        self.add_combat_log(f"👹 {attack_msg}")
        self.add_combat_log(f"⚔️ Attack deals {base_damage} damage (accumulated: {self.accumulated_damage})")
        
        # Increment attack count
        self.current_attack_count += 1
        
        # Check if enemy has more attacks this turn
        if self.current_attack_count < self.enemy_attacks_per_turn:
            # Continue attacking after a shorter delay
            if self.current_attack_count < self.enemy_attacks_per_turn - 1:
                self.add_combat_log(f"💫 {self.current_enemy.name} prepares another strike...")
            self.root.after(1000, self.enemy_turn)
            return
        
        # All attacks done - now apply defense and resolve damage
        self.resolve_accumulated_damage(player_defense)
        
        # Reset for next turn
        self.accumulated_damage = 0
        self.current_attack_count = 0
        self.player_turn = True
        self.attack_btn.config(state=tk.NORMAL)
        self.flee_btn.config(state=tk.NORMAL)

    def resolve_accumulated_damage(self, player_defense):
        """Resolve accumulated damage against player defense with variance"""
        # Add player null check at the beginning
        if not hasattr(self, 'player') or self.player is None:
            self.add_combat_log(f"❌ No player found during damage resolution!")
            return
        
        if not hasattr(self, 'accumulated_damage') or self.accumulated_damage <= 0:
            self.add_combat_log(f"🛡️ No damage to resolve!")
            return
        
        # Calculate base damage after defense
        base_damage_after_defense = max(0, self.accumulated_damage - player_defense)
        
        # Add variance: ±25% of the base damage (minimum 0)
        if base_damage_after_defense > 0:
            variance_range = max(1, int(base_damage_after_defense * 0.25))
            variance = random.randint(-variance_range, variance_range)
            final_damage = max(0, base_damage_after_defense + variance)
            
            # Ensure at least some damage gets through occasionally even with high defense
            if final_damage == 0 and self.accumulated_damage > 0:
                # 10% chance for 1 damage to slip through even with perfect defense
                if random.randint(1, 100) <= 10:
                    final_damage = 1
                    self.add_combat_log(f"💢 A lucky hit slips through your defense!")
        else:
            final_damage = 0
        
        # Apply the final damage
        if final_damage > 0:
            self.player.health -= final_damage
            self.add_combat_log(f"🛡️ Defense blocks {player_defense} damage! You take {final_damage} damage!")
            
            # Show damage calculation details
            if base_damage_after_defense != final_damage:
                if final_damage > base_damage_after_defense:
                    self.add_combat_log(f"💔 Unlucky! Variance increased damage by {final_damage - base_damage_after_defense}")
                else:
                    self.add_combat_log(f"🍀 Lucky! Variance reduced damage by {base_damage_after_defense - final_damage}")
        else:
            self.add_combat_log(f"🛡️ Your defense of {player_defense} completely blocks all {self.accumulated_damage} damage!")
        
        # Update player health display - add safety check for UI element
        if hasattr(self, 'player_health_label') and self.player_health_label.winfo_exists():
            self.player_health_label.config(text=f"❤️ HP: {self.player.health}/{self.player.max_health}")
        
        # Check if player is defeated
        if self.player.health <= 0:
            self.combat_defeat()
            return
        
        # Log the round summary
        self.add_combat_log(f"📊 Round Summary: {self.accumulated_damage} total attack vs {player_defense} defense = {final_damage} damage taken")

    def attempt_flee(self):
        """Attempt to flee from combat with base 25% chance minimum"""
        if not hasattr(self, 'current_enemy') or self.current_enemy is None:
            return
        
        player_stats = self.player.get_total_stats()
        player_speed = player_stats['speed']
        enemy_speed = self.current_enemy.speed
        
        # Base 25% flee chance regardless of speed difference
        base_flee_chance = 25
        
        # Speed difference bonus/penalty
        speed_difference = player_speed - enemy_speed
        speed_bonus = speed_difference * 2  # 2% per speed point difference
        
        # Calculate total flee chance (minimum 25%, maximum 95%)
        flee_chance = max(25, min(95, base_flee_chance + speed_bonus))
        
        # Roll for flee attempt
        roll = random.randint(1, 100)
        
        if roll <= flee_chance:
            # Successful flee
            flee_message = f"💨 You successfully fled from the {self.current_enemy.name}!"
            
            if speed_difference >= 10:
                flee_message += " (Easy escape due to superior speed!)"
            elif speed_difference <= -10:
                flee_message += " (Lucky escape despite being slower!)"
            
            self.add_combat_log(flee_message)  # Use add_combat_log for combat window
            self.log_message(flee_message)     # Also log to main game log
            self.close_combat_window()
        else:
            # Failed flee attempt
            fail_message = f"❌ Failed to flee! The {self.current_enemy.name} blocks your escape!"
            
            if speed_difference <= -10:
                fail_message += " (Too slow to outrun this enemy!)"
            
            self.add_combat_log(fail_message)  # Use add_combat_log for combat window
            self.log_message(fail_message)     # Also log to main game log
            
            # Enemy gets a free attack after failed flee
            self.add_combat_log("💀 The enemy attacks while you're vulnerable!")
            self.enemy_turn()  # Changed from enemy_attack() to enemy_turn()

    def combat_victory(self):
        """Player wins the combat"""
        if not hasattr(self, 'current_enemy'):
            return
        if not hasattr(self, 'player') or self.player is None:
            return
        self.add_combat_log(f"🎉 Victory! You defeated {self.current_enemy.name}!")
        
        # Rewards
        gold_reward = self.current_enemy.loot_value
        xp_reward = self.current_enemy.xp_reward
               
        self.player.gold += gold_reward
        # Add XP and check for level up
        level_up_message = self.player.add_xp(xp_reward)

        self.add_combat_log(f"💰 You earned {gold_reward} gold!")
        if xp_reward > 0:
            self.add_combat_log(f"⭐ You gained {xp_reward} experience!")
        
        # Log victory in main game log
        self.log_message(f"⚔️ Defeated {self.current_enemy.name}! Earned {gold_reward} gold.")
        if level_up_message:
            self.log_message(f"🎉 {level_up_message}")

        if level_up_message:
            self.root.after(2000, lambda: self.end_combat_then_level_up(level_up_message))
        else:
            self.root.after(1500, self.end_combat)

    def combat_defeat(self):
        """Player loses the combat"""
        if not hasattr(self, 'current_enemy') or not self.current_enemy.is_alive():
            return
        if not hasattr(self, 'player') or self.player is None:
            return
        
        self.add_combat_log(f"💀 Defeat! {self.current_enemy.name} has defeated you!")
        
        # CHANGED: Don't set health to 1, leave it at 0 for proper game over
        # The player's health should already be 0 or below from the damage
        if self.player.health > 0:
            self.player.health = 0  # Ensure player is actually defeated
        
        # Penalties for losing - but only if not completely dead
        gold_lost = min(self.player.gold, self.player.gold // 4)  # Lose 25% of gold
        self.player.gold -= gold_lost
        self.player.add_xp(-self.current_enemy.xp_reward // 2)  # Lose half XP
        self.add_combat_log(f"💸 You lost {gold_lost} gold.")
        self.add_combat_log(f"💀 Your adventure ends here...")
        
        # Log the defeat
        self.log_message(f"💀 GAME OVER! Defeated by {self.current_enemy.name}!")
        
        # End combat and trigger game over
        self.root.after(3000, self.end_combat_with_game_over)

    def close_combat_window(self):
        """Close the combat window and return to main game"""
        if hasattr(self, 'combat_window') and self.combat_window.winfo_exists():
            self.combat_window.destroy()
        
        # Clean up combat variables
        if hasattr(self, 'current_enemy'):
            delattr(self, 'current_enemy')
        if hasattr(self, 'combat_log'):
            delattr(self, 'combat_log')
        
        # Update main UI
        self.update_player_info()

    def end_combat_then_level_up(self, level_up_message):
        """End combat then show level up choice"""
        self.end_combat()
        # Small delay before showing level up window
        self.root.after(500, lambda: self.show_level_up_choice(level_up_message))

    def end_combat_with_game_over(self):
        """End combat and immediately show game over screen"""
        if hasattr(self, 'combat_window') and self.combat_window.winfo_exists():
            self.combat_window.destroy()
        
        # Clean up combat variables
        if hasattr(self, 'current_enemy'):
            delattr(self, 'current_enemy')
        if hasattr(self, 'combat_log'):
            delattr(self, 'combat_log')
        
        # Show game over screen immediately
        self.show_game_over_screen()

    def end_combat(self):
        """End combat and return to main game"""
        if hasattr(self, 'combat_window') and self.combat_window.winfo_exists():
            self.combat_window.destroy()
        
        # Update main UI
        self.update_player_info()
        
        # Clean up combat variables
        if hasattr(self, 'current_enemy'):
            delattr(self, 'current_enemy')
        if hasattr(self, 'combat_log'):
            delattr(self, 'combat_log')

    def show_level_up_choice(self, level_up_message):
        """Show level up stat choice window - simplified to +1 single stat only"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # Create level up window
        level_window = tk.Toplevel(self.root)
        level_window.title("🎉 LEVEL UP!")
        level_window.geometry("600x800")
        level_window.configure(bg="#FFD700")
        level_window.transient(self.root)
        level_window.grab_set()
        
        # Celebration title
        title_label = tk.Label(level_window, text="🎉 LEVEL UP! 🎉", 
                            font=("Helvetica", 20, "bold"), bg="#FFD700", fg="#8B4513")
        title_label.pack(pady=15)
        
        # Level up message
        message_label = tk.Label(level_window, text=level_up_message, 
                                font=("Helvetica", 14), bg="#FFD700", fg="#8B4513")
        message_label.pack(pady=5)
        
        # Choice instruction
        choice_label = tk.Label(level_window, text="Choose which stat to increase by +1:", 
                            font=("Helvetica", 14, "bold"), bg="#FFD700", fg="#8B4513")
        choice_label.pack(pady=10)
        
        # Current stats display
        stats = self.player.get_total_stats()
        stats_text = f"Current Stats:\n🍀 Luck: {stats['luck']} → {stats['luck'] + 1}\n⚔️ Attack: {stats['attack']} → {stats['attack'] + 1}\n🛡️ Defense: {stats['defense']} → {stats['defense'] + 1}\n💨 Speed: {stats['speed']} → {stats['speed'] + 1}"
        
        stats_display = tk.Label(level_window, text=stats_text, 
                                font=("Helvetica", 11), bg="#FFD700", fg="#4B0082",
                                justify=tk.CENTER)
        stats_display.pack(pady=15)
        
        # Button frame
        button_frame = tk.Frame(level_window, bg="#FFD700")
        button_frame.pack(pady=20)
        
        # Single stat buttons (+1 each)
        luck_btn = tk.Button(button_frame, text="🍀 +1 Luck", 
                            font=("Helvetica", 12, "bold"), bg="#FFD700", fg="black",
                            command=lambda: self.apply_level_bonus("luck", 1, level_window),
                            width=12, height=2)
        luck_btn.pack(pady=5)
        
        attack_btn = tk.Button(button_frame, text="⚔️ +1 Attack", 
                            font=("Helvetica", 12, "bold"), bg="#FF4444", fg="white",
                            command=lambda: self.apply_level_bonus("attack", 1, level_window),
                            width=12, height=2)
        attack_btn.pack(pady=5)
        
        defense_btn = tk.Button(button_frame, text="🛡️ +1 Defense", 
                            font=("Helvetica", 12, "bold"), bg="#4444FF", fg="white",
                            command=lambda: self.apply_level_bonus("defense", 1, level_window),
                            width=12, height=2)
        defense_btn.pack(pady=5)
        
        speed_btn = tk.Button(button_frame, text="💨 +1 Speed", 
                            font=("Helvetica", 12, "bold"), bg="#44FF44", fg="black",
                            command=lambda: self.apply_level_bonus("speed", 1, level_window),
                            width=12, height=2)
        speed_btn.pack(pady=5)
    
    def apply_level_bonus(self, stat, amount, level_window):
        """Apply single stat bonus using existing increase_stat logic"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # Use existing increase_stat logic from Trade class
        if stat == "luck":
            self.player.base_luck += amount
            bonus_text = f"+{amount} 🍀 Luck"
        elif stat == "attack":
            self.player.base_attack += amount
            bonus_text = f"+{amount} ⚔️ Attack"
        elif stat == "defense":
            self.player.base_defense += amount
            bonus_text = f"+{amount} 🛡️ Defense"
        elif stat == "speed":
            self.player.base_speed += amount
            bonus_text = f"+{amount} 💨 Speed"
        else:
            bonus_text = "Unknown stat"
        
        # Log the bonus
        self.log_message(f"📈 Level {self.player.level} bonus: {bonus_text}")
        
        # Update displays
        self.update_player_info()
        
        # Close level up window
        level_window.destroy()
        
        # Show confirmation
        messagebox.showinfo("Level Up Complete!", f"Level {self.player.level} bonus applied:\n{bonus_text}")
    
    def open_trade_window(self):
        """Open trade window to buy trades with gold"""
        if not hasattr(self, 'player') or self.player is None:
            return

        # FIXED: Check for trade_window instead of gear_window
        if hasattr(self, 'trade_window') and self.trade_window.winfo_exists():
            self.trade_window.lift()  # Bring existing window to front
            return
        
        # FIXED: Disable trade_btn instead of gear_btn
        if hasattr(self, 'trade_btn'):
            self.trade_btn.config(state=tk.DISABLED)
            self.root.after(1000, lambda: self.trade_btn.config(state=tk.NORMAL))

        # Check if player has energy to trade
        if not self.player.can_fish():  # Using can_fish() since it checks energy > 0
            messagebox.showwarning("No Energy", "You need at least 1 energy to trade!")
            return

        # Filter trades based on level requirement AND quantity remaining
        available_trades_for_level = []
        for trade_data in self.trade_data['trade']:
            level_requirement = trade_data.get('level_requirement', 1)  # Default to level 1 if not specified
            
            # Check level requirement
            if self.player.level < level_requirement:
                continue
                
            # NEW: Check if trade still has quantity remaining
            remaining = self.player.get_remaining_trades(trade_data["name"], trade_data)
            if remaining > 0:  # Only include trades with quantity left
                available_trades_for_level.append(trade_data)

        # Generate 3 random trade options from FILTERED list
        if not hasattr(self, 'current_trade_options') or not self.current_trade_options:
            if len(available_trades_for_level) < 3:
                # If less than 3 trades available for level, show all available
                if len(available_trades_for_level) == 0:
                    messagebox.showinfo("No Trades Available", 
                                    f"No trades available for level {self.player.level}!\n"
                                    f"All trades may be exhausted or level too low.")
                    return
                else:
                    # Show all available trades if less than 3
                    selected_trades = available_trades_for_level
            else:
                # Use filtered list instead of self.trade_data['trade']
                selected_trades = random.sample(available_trades_for_level, 3)
            
            self.current_trade_options = [Trade(trade_data) for trade_data in selected_trades]

        # Create new window
        self.trade_window = tk.Toplevel(self.root)
        self.trade_window.title("Trade Deck")
        self.trade_window.geometry("800x700")
        self.trade_window.configure(bg="#F5F5DC")

        # Window title
        title_label = tk.Label(self.trade_window, text="🎴 Trade Deck - Choose Wisely!", 
                        font=("Helvetica", 18, "bold"), bg="#F5F5DC")
        title_label.pack(pady=10)

        # Current gold and energy display
        info_frame = tk.Frame(self.trade_window, bg="#F5F5DC")
        info_frame.pack(pady=5)

        gold_label = tk.Label(info_frame, text=f"Current Gold: {self.player.gold}g", 
                        font=("Helvetica", 14), bg="#F5F5DC", fg="green")
        gold_label.pack(side=tk.LEFT, padx=10)

        energy_label = tk.Label(info_frame, text=f"Energy: {self.player.energy}", 
                        font=("Helvetica", 14), bg="#F5F5DC", fg="blue")
        energy_label.pack(side=tk.LEFT, padx=10)

        # Energy cost info
        cost_label = tk.Label(self.trade_window, text="💡 Trading costs 1 energy per session", 
                        font=("Helvetica", 11), bg="#F5F5DC", fg="gray")
        cost_label.pack(pady=5)

        # Trade options frame
        trades_frame = tk.Frame(self.trade_window, bg="#F5F5DC")
        trades_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create 3 trade option cards
        for i, trade in enumerate(self.current_trade_options):
            self.create_trade_card(trades_frame, trade, i)

        # Close button
        close_button = tk.Button(self.trade_window, text="Close", 
                            font=("Helvetica", 12), bg="#757575", fg="white",
                            command=self.trade_window.destroy)
        close_button.pack(pady=10)

    def create_trade_card(self, parent, trade, index):
        """Create a trade card UI element"""
        if not hasattr(self, 'player') or self.player is None:
            return
            
        # Find the original trade data to get level requirement and quantity info
        level_requirement = 1  # Default
        max_quantity = 1  # Default
        for trade_data in self.trade_data['trade']:
            if trade_data['name'] == trade.name:
                level_requirement = trade_data.get('level_requirement', 1)
                max_quantity = trade_data.get('quantity', 1)
                break
        
        # Get remaining quantity
        remaining = self.player.get_remaining_trades(trade.name, {"quantity": max_quantity})
        
        # Main card frame
        card_frame = tk.Frame(parent, bg="#FFFFFF", relief=tk.RAISED, bd=2)
        card_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Trade header
        header_frame = tk.Frame(card_frame, bg="#E3F2FD")
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        trade_name = tk.Label(header_frame, text=f"🎴 {trade.name}", 
                            font=("Helvetica", 14, "bold"), bg="#E3F2FD")
        trade_name.pack(side=tk.LEFT)
        
        trade_type = tk.Label(header_frame, text=f"[{trade.trade_type}]", 
                            font=("Helvetica", 12), bg="#E3F2FD", fg="gray")
        trade_type.pack(side=tk.RIGHT)
        
        # Trade effect description
        effect_label = tk.Label(card_frame, text=trade.effect, 
                            font=("Helvetica", 12), bg="#FFFFFF", 
                            wraplength=400, justify=tk.LEFT)
        effect_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # Bottom frame with price, quantity, and button
        bottom_frame = tk.Frame(card_frame, bg="#FFFFFF")
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Price and quantity display
        price_label = tk.Label(bottom_frame, text=f"💰 Cost: {trade.gold_value}g", 
                            font=("Helvetica", 12, "bold"), bg="#FFFFFF", fg="green")
        price_label.pack(side=tk.LEFT)
        
        # NEW: Show remaining quantity
        quantity_label = tk.Label(bottom_frame, text=f"📦 Remaining: {remaining}", 
                                font=("Helvetica", 11), bg="#FFFFFF", 
                                fg="darkgreen" if remaining > 0 else "red")
        quantity_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Buy button
        can_afford = self.player.gold >= trade.gold_value
        has_quantity = remaining > 0
        
        if not has_quantity:
            button_color = "#CCCCCC"
            button_text = "Sold Out"
            button_state = tk.DISABLED
        elif not can_afford:
            button_color = "#CCCCCC"
            button_text = "Can't Afford"
            button_state = tk.DISABLED
        else:
            button_color = "#4CAF50"
            button_text = "💰 Buy This Trade"
            button_state = tk.NORMAL
        
        buy_button = tk.Button(bottom_frame, text=button_text, 
                            font=("Helvetica", 12), bg=button_color, fg="white",
                            command=lambda t=trade: self.execute_trade(t),
                            state=button_state)
        buy_button.pack(side=tk.RIGHT)

    def execute_trade(self, trade):
        """Execute a selected trade"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # NEW: Check if trade still has quantity available
        max_quantity = 1  # Default
        for trade_data in self.trade_data['trade']:
            if trade_data['name'] == trade.name:
                max_quantity = trade_data.get('quantity', 1)
                break
        
        if not self.player.can_purchase_trade(trade.name, {"quantity": max_quantity}):
            messagebox.showwarning("Trade Unavailable", f"{trade.name} is no longer available!")
            return
        
        # Check if player can afford the trade
        if self.player.gold < trade.gold_value:
            messagebox.showwarning("Cannot Afford", f"You need {trade.gold_value}g but only have {self.player.gold}g!")
            return
        
        # Check if player has energy
        if not self.player.can_fish():
            messagebox.showwarning("No Energy", "You need at least 1 energy to trade!")
            return
        
        # NEW: Check if player only has 1 energy left and confirm
        if self.player.energy == 1:
            confirm = messagebox.askyesno("Last Energy Warning", 
                                        "⚠️ You only have 1 energy left!\n\n"
                                        "Trading will use your last energy and end your adventure.\n\n"
                                        "Are you sure you want to make this trade?",
                                        icon='warning')
            if not confirm:
                return  # Player chose not to trade

        # Confirm trade
        confirm = messagebox.askyesno("Confirm Trade", 
                                    f"Buy '{trade.name}' for {trade.gold_value}g?\n\nEffect: {trade.effect}\n(Costs 1 energy)")
        if not confirm:
            return
        
        # Use energy for trading
        if not self.player.use_energy(1):
            messagebox.showwarning("No Energy", "You don't have enough energy to trade!")
            return
        
        # Deduct gold
        self.player.gold -= trade.gold_value
        
        # NEW: Record the trade usage
        self.player.use_trade(trade.name)
        
        # Execute trade effect using the existing Trade class method
        result = trade.execute_trigger(self.player, self)
        
        # Add to completed trades for location unlocking
        if trade.name not in self.player.completed_trades:
            self.player.completed_trades.append(trade.name)
        
        # IMPORTANT FIX: Check for location unlocking and update dropdown
        if "unlock_location" in str(trade.trigger):
            # Force update the location dropdown immediately
            self.update_location_dropdown()
            
            # Also add specific unlock keys for the locations.json checking
            triggers = trade.trigger if isinstance(trade.trigger, list) else [trade.trigger]
            for trigger in triggers:
                if trigger.get("action") == "unlock_location":
                    location_name = trigger.get("target", "")
                    if location_name:
                        # Add the specific unlock key that Location.is_unlocked() checks for
                        location_key = f"unlocked_{location_name.lower().replace(' ', '_')}"
                        if location_key not in self.player.completed_trades:
                            self.player.completed_trades.append(location_key)

        # Clear current trade options so new ones are generated next time
        self.current_trade_options = []

        # Log the trade
        self.log_message(f"🎴 Traded for '{trade.name}' for {trade.gold_value}g! (-1 energy)")
        self.log_message(f"   ✨ {result}")
        
        # Check for game over due to energy loss
        if self.player.is_game_over():
            self.log_message("💀 GAME OVER! You ran out of energy!")
            self.trade_window.destroy()
            self.root.after(1000, self.show_game_over_screen)
            return
        
        # Update displays
        self.update_player_info()
        
        # Close trade window and show success
        self.trade_window.destroy()
        messagebox.showinfo("Trade Complete", f"Successfully traded for '{trade.name}'!\n\n{result}")

    def start_game(self):
        """Start character creation process"""
        self.title_label.pack_forget()
        self.start_button.pack_forget()
        self.quit_button.pack_forget()
        self.create_character_setup()

    def create_character_setup(self):
        """Create character setup interface"""
        self.setup_frame = tk.Frame(self.root, bg="#87CEEB")
        self.setup_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        # Title
        setup_title = tk.Label(self.setup_frame, text="Create Your Fisher",
                              font=("Helvetica", 24, "bold"), bg="#87CEEB")
        setup_title.pack(pady=(0, 30))

        # Name input section
        name_section = tk.Frame(self.setup_frame, bg="#87CEEB")
        name_section.pack(pady=(0, 30))

        name_label = tk.Label(name_section, text="Enter your name:",
                             font=("Helvetica", 16), bg="#87CEEB")
        name_label.pack(pady=(0, 10))

        # Name entry and random button frame
        name_frame = tk.Frame(name_section, bg="#87CEEB")
        name_frame.pack()

        self.name_entry = tk.Entry(name_frame, font=("Helvetica", 14), width=25)
        self.name_entry.pack(side=tk.LEFT, padx=(0, 10))

        random_name_btn = tk.Button(name_frame, text="🎲 Random Name", 
                               font=("Helvetica", 12), bg="#FF9800", fg="white",
                               command=self.generate_random_name)
        random_name_btn.pack(side=tk.LEFT)

        # Start adventure button
        start_adventure_btn = tk.Button(self.setup_frame, text="Begin Your Adventure!", 
                               font=("Helvetica", 16), bg="#4CAF50", fg="white",
                               command=self.begin_adventure)
        start_adventure_btn.pack(pady=20)

    def generate_random_name(self):
        """Generate a random fisher name"""
        first_names = [
            "Fisher", "Marina", "River", "Brook", "Captain", "Sailor", "Admiral", "Pike", 
            "Bass", "Finn", "Rod", "Reel", "Anchor", "Tide", "Storm", "Wave", "Current",
            "Depth", "Coral", "Pearl", "Shell", "Drift", "Harbor", "Bay", "Coast",
            "Reef", "Marlin", "Tuna", "Cod", "Salmon", "Trout", "Carp", "Minnow",
            "Whale", "Shark", "Ray", "Eel", "Crab", "Lobster", "Shrimp", "Kelp","Cthulu","Stinky","Big","Fishy","Bubbles","Splash","Gills","Finley","Hook","Reelina","Tidal","Nautical","Muhammad","Jesus","Lil", "Truck", "Big Back", "Ford", "Tyler", "Bubba", "Koda", "Marco", "Duke", "Splash", "Gilligan", "Dick", "Philly", "Sarah", "Flounder"
        ]
        
        last_names = [
            "Angler", "Caster", "Fisher", "Netsman", "Hooker", "Baiter", "Reeler",
            "Sailor", "Mariner", "Seaman", "Captain", "Navigator", "Helmsman",
            "Tidewatcher", "Stormrider", "Wavebreaker", "Deepdiver", "Surfcaster",
            "Linecaster", "Rodmaster", "Baitlord", "Catchall", "Bigfish", "Longline",
            "Sinker", "Floater", "Dragnetter", "Spearman", "Harpoon", "Tackle",
            "Lighthouse", "Portside", "Starboard", "Windward", "Leeward", "Offshore","Cthulu","Jackson","Texas", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez", "Davis", "Rodriguez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Perez", "Big Back", "Buster", "Military", "Taylor", "Chimichanga"
        ]
        
        random_first = random.choice(first_names)
        random_last = random.choice(last_names)
        random_name = f"{random_first} {random_last}"
        
        # Clear current name and insert random name
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, random_name)

        # Replace the open_sell_window method:
    
    def open_sell_window(self):
        """Open sell window to sell items for gold"""
        if not hasattr(self, 'player') or self.player is None:
            return

        # Prevent multiple sell windows
        if hasattr(self, 'sell_window') and self.sell_window.winfo_exists():
            self.sell_window.lift()  # Bring existing window to front
            return
        
        # Disable sell button temporarily
        if hasattr(self, 'sell_btn'):
            self.sell_btn.config(state=tk.DISABLED)
            self.root.after(1000, lambda: self.sell_btn.config(state=tk.NORMAL))

        # Create new window
        self.sell_window = tk.Toplevel(self.root)
        self.sell_window.title("Sell Items")
        self.sell_window.geometry("700x600")
        self.sell_window.configure(bg="#F0F8FF")

        # Window title
        title_label = tk.Label(self.sell_window, text="💰 Sell Items for Gold", 
                              font=("Helvetica", 18, "bold"), bg="#F0F8FF")
        title_label.pack(pady=10)
        
        # Current gold and energy display
        info_frame = tk.Frame(self.sell_window, bg="#F0F8FF")
        info_frame.pack(pady=5)
        
        gold_label = tk.Label(info_frame, text=f"Current Gold: {self.player.gold}g", 
                             font=("Helvetica", 14), bg="#F0F8FF", fg="green")
        gold_label.pack(side=tk.LEFT, padx=10)
        
        energy_label = tk.Label(info_frame, text=f"Energy: {self.player.energy}/{self.player.max_energy}", 
                               font=("Helvetica", 14), bg="#F0F8FF", fg="blue")
        energy_label.pack(side=tk.LEFT, padx=10)
        
        # Energy cost info
        cost_label = tk.Label(self.sell_window, text="💡 Selling costs 1 energy per session (select multiple items!)", 
                             font=("Helvetica", 11), bg="#F0F8FF", fg="gray")
        cost_label.pack(pady=5)
                
        # Sellable items listbox
        items_label = tk.Label(self.sell_window, text="Select item(s) to sell:", 
                              font=("Helvetica", 12, "bold"), bg="#F0F8FF")
        items_label.pack(pady=(10, 5))
        
        # Frame for listbox and scrollbar
        listbox_frame = tk.Frame(self.sell_window, bg="#F0F8FF")
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Listbox with scrollbar (allow multiple selections)
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.sell_listbox = tk.Listbox(listbox_frame, font=("Helvetica", 11), 
                                       yscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE)
        self.sell_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.sell_listbox.yview)
        
        # Store sellable items for reference
        self.sellable_items = []
        
        # Add fish to sell list
        for item in self.player.inventory:
            if hasattr(item, 'get_sell_value'):  # It's a fish
                sell_value = item.get_sell_value()
                display_text = f"🐟 {item.name} ({item.actual_size}in) - {sell_value}g"
                self.sell_listbox.insert(tk.END, display_text)
                self.sellable_items.append(('fish', item, sell_value))
        
        # Add items to sell list
        for item in self.player.inventory:
            if hasattr(item, 'value') and not hasattr(item, 'get_sell_value'):  # Regular items
                display_text = f"📦 {item.name} ({item.item_type}) - {item.value}g"
                self.sell_listbox.insert(tk.END, display_text)
                self.sellable_items.append(('item', item, item.value))
        
        # Add gear to sell list (only unequipped gear)
        for gear in self.player.gear_inventory:
            if not gear.equipped:
                display_text = f"⚔️ {gear.name} [{gear.gear_type}] - {gear.gold_value}g"
                self.sell_listbox.insert(tk.END, display_text)
                self.sellable_items.append(('gear', gear, gear.gold_value))
        
        # If no items to sell
        if not self.sellable_items:
            self.sell_listbox.insert(tk.END, "No items available to sell!")
        
        # Buttons frame
        button_frame = tk.Frame(self.sell_window, bg="#F0F8FF")
        button_frame.pack(pady=20)
        
        # Sell selected button
        sell_selected_button = tk.Button(button_frame, text="💰 Sell Selected Items", 
                                        font=("Helvetica", 12), bg="#4CAF50", fg="white",
                                        command=self.sell_selected_items)
        sell_selected_button.pack(side=tk.LEFT, padx=5)
        
        # Sell all button
        sell_all_button = tk.Button(button_frame, text="🔥 Sell All Items", 
                                   font=("Helvetica", 12), bg="#FF5722", fg="white",
                                   command=self.sell_all_items)
        sell_all_button.pack(side=tk.LEFT, padx=5)
        
        # Select all button
        select_all_button = tk.Button(button_frame, text="📋 Select All", 
                                     font=("Helvetica", 12), bg="#2196F3", fg="white",
                                     command=self.select_all_items)
        select_all_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = tk.Button(button_frame, text="Close", 
                                font=("Helvetica", 12), bg="#757575", fg="white",
                                command=self.sell_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

    def select_all_items(self):
        """Select all items in the sell listbox"""
        if self.sellable_items:
            self.sell_listbox.select_set(0, tk.END)
    
    def sell_selected_items(self):
        """Sell all selected items from the sell window"""
        if not hasattr(self, 'player') or self.player is None:
            return
        selections = self.sell_listbox.curselection()
        
        if not selections:
            messagebox.showwarning("No Selection", "Please select item(s) to sell!")
            return
        
        # Check if player has energy to sell
        if not self.player.can_fish():  # Using can_fish() since it checks energy > 0
            messagebox.showwarning("No Energy", "You need at least 1 energy to sell items!")
            return
        
        # Calculate total value
        total_gold = 0
        items_to_sell = []
        
        for index in selections:
            if index < len(self.sellable_items):
                item_type, item, gold_value = self.sellable_items[index]
                total_gold += gold_value
                items_to_sell.append((item_type, item, gold_value))
        
        if not items_to_sell:
            return
        
        # Confirm sale with energy cost
        item_count = len(items_to_sell)
        confirm = messagebox.askyesno("Confirm Sale", 
                                     f"Sell {item_count} item(s) for {total_gold} total gold?\n(Costs 1 energy)")
        if not confirm:
            return
        
        # Use energy for selling session
        if not self.player.use_energy(1):
            messagebox.showwarning("No Energy", "You don't have enough energy to sell!")
            return
        
        # Sell all selected items
        sold_items = []
        for item_type, item, gold_value in items_to_sell:
            if item_type == 'fish':
                if item in self.player.inventory:
                    self.player.inventory.remove(item)
                    self.player.gold += gold_value
                    sold_items.append(f"{item.name} ({gold_value}g)")
            
            elif item_type == 'item':
                if item in self.player.inventory:
                    self.player.inventory.remove(item)
                    self.player.gold += gold_value
                    sold_items.append(f"{item.name} ({gold_value}g)")
            
            elif item_type == 'gear':
                if item in self.player.gear_inventory:
                    self.player.gear_inventory.remove(item)
                    self.player.gold += gold_value
                    sold_items.append(f"{item.name} ({gold_value}g)")
        
        # Log the sales
        self.log_message(f"💰 Sold {len(sold_items)} items for {total_gold} total gold! (-1 energy)")
        if len(sold_items) <= 5:  # Show individual items if not too many
            for item_name in sold_items:
                self.log_message(f"   • {item_name}")
        
        # Check if game is over due to energy loss
        if self.player.is_game_over():
            self.log_message("💀 GAME OVER! You ran out of energy!")
        
        # Update displays
        self.update_player_info()
        
        # Close and reopen sell window to refresh the list
        self.sell_window.destroy()
        self.open_sell_window()
    
    def sell_all_items(self):
        """Sell all available items"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        if not self.sellable_items:
            messagebox.showinfo("No Items", "No items available to sell!")
            return
        
        if not self.player.can_fish():
            messagebox.showwarning("No Energy", "You need at least 1 energy to sell items!")
            return
        
        # Calculate total value
        total_gold = sum(item[2] for item in self.sellable_items)
        item_count = len(self.sellable_items)
        
        # Confirm sale
        confirm = messagebox.askyesno("Confirm Sell All", 
                                     f"Sell ALL {item_count} items for {total_gold} total gold?\n(Costs 1 energy)")
        if not confirm:
            return
        
        # Use energy for selling session
        if not self.player.use_energy(1):
            messagebox.showwarning("No Energy", "You don't have enough energy to sell!")
            return
        
        # Sell all items
        sold_items = []
        for item_type, item, gold_value in self.sellable_items:
            if item_type == 'fish':
                if item in self.player.inventory:
                    self.player.inventory.remove(item)
                    self.player.gold += gold_value
                    sold_items.append(item.name)
            
            elif item_type == 'item':
                if item in self.player.inventory:
                    self.player.inventory.remove(item)
                    self.player.gold += gold_value
                    sold_items.append(item.name)
            
            elif item_type == 'gear':
                if item in self.player.gear_inventory:
                    self.player.gear_inventory.remove(item)
                    self.player.gold += gold_value
                    sold_items.append(item.name)
        
        # Log the sales
        self.log_message(f"🔥 SOLD ALL! {len(sold_items)} items for {total_gold} total gold! (-1 energy)")
        
        # Check if game is over due to energy loss
        if self.player.is_game_over():
            self.log_message("💀 GAME OVER! You ran out of energy!")
            self.sell_window.destroy()  # Close sell window first
            self.root.after(1000, self.show_game_over_screen)
            return
        
        # Update displays
        self.update_player_info()
        
        # Close sell window
        self.sell_window.destroy()

    def open_inventory_window(self):
        """Open inventory window when player name is clicked"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # Create new window
        self.inventory_window = tk.Toplevel(self.root)
        self.inventory_window.title(f"{self.player.name}'s Inventory")
        self.inventory_window.geometry("800x600")
        self.inventory_window.configure(bg="#F0F8FF")
    
        # Window title
        title_label = tk.Label(self.inventory_window, text=f"{self.player.name}'s Inventory", 
                          font=("Helvetica", 18, "bold"), bg="#F0F8FF")
        title_label.pack(pady=10)
    
        # Create notebook for tabs
        from tkinter import ttk
        notebook = ttk.Notebook(self.inventory_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
        # Fish Tab
        fish_frame = tk.Frame(notebook, bg="#F0F8FF")
        notebook.add(fish_frame, text="🐟 Fish")
    
        fish_label = tk.Label(fish_frame, text="Caught Fish:", 
                         font=("Helvetica", 14, "bold"), bg="#F0F8FF")
        fish_label.pack(pady=5)
    
        fish_listbox = tk.Listbox(fish_frame, font=("Helvetica", 10), height=15)
        fish_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
        # Add fish to listbox
        fish_count = 0
        for item in self.player.inventory:
            if hasattr(item, 'actual_size'):  # It's a fish
                effect_text = ""
                if hasattr(item, 'fish_effect') and item.fish_effect != "none":
                    effect_text = f" [✨ {item.fish_effect}]"
                
                display_text = f"{item.name} ({item.actual_size}in) - {item.get_sell_value()}g{effect_text}"
                fish_listbox.insert(tk.END, display_text)
                fish_count += 1
    
        if fish_count == 0:
            fish_listbox.insert(tk.END, "No fish caught yet!")
    
        # Items Tab
        items_frame = tk.Frame(notebook, bg="#F0F8FF")
        notebook.add(items_frame, text="📦 Items")
    
        items_label = tk.Label(items_frame, text="Found Items:", 
                          font=("Helvetica", 14, "bold"), bg="#F0F8FF")
        items_label.pack(pady=5)
    
        items_listbox = tk.Listbox(items_frame, font=("Helvetica", 10), height=15)
        items_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
        # Add items to listbox
        item_count = 0
        for item in self.player.inventory:
            if hasattr(item, 'item_type'):  # It's an item
                items_listbox.insert(tk.END, f"{item.name} ({item.item_type}) - {item.value}g")
                item_count += 1
    
        if item_count == 0:
            items_listbox.insert(tk.END, "No items found yet!")
    
        fish_button_frame = tk.Frame(fish_frame, bg="#F0F8FF")
        fish_button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        eat_fish_btn = tk.Button(fish_button_frame, text="🍽️ Eat Selected Fish", 
                                font=("Helvetica", 12), bg="#FF8C00", fg="white",
                                command=lambda: self.eat_selected_fish(fish_listbox))
        eat_fish_btn.pack(side=tk.LEFT, padx=5)

        # Gear Tab
        gear_frame = tk.Frame(notebook, bg="#F0F8FF")
        notebook.add(gear_frame, text="⚔️ Gear")
    
        gear_label = tk.Label(gear_frame, text="Equipment:", 
                         font=("Helvetica", 14, "bold"), bg="#F0F8FF")
        gear_label.pack(pady=5)
    
        gear_listbox = tk.Listbox(gear_frame, font=("Helvetica", 10), height=15)
        gear_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
        # Add gear to listbox
        if len(self.player.gear_inventory) > 0:
            for gear in self.player.gear_inventory:
                equipped_text = " [EQUIPPED]" if gear.equipped else ""
                bonus_text = ""
                if gear.stat_bonus:
                    bonus_list = [f"+{value} {stat}" for stat, value in gear.stat_bonus.items()]
                    bonus_text = f" ({', '.join(bonus_list)})"
                gear_listbox.insert(tk.END, f"{gear.name} [{gear.gear_type}]{bonus_text} - {gear.gold_value}g{equipped_text}")
        else:
            gear_listbox.insert(tk.END, "No gear found yet!")

        # Add gear action buttons
        gear_button_frame = tk.Frame(gear_frame, bg="#F0F8FF")
        gear_button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        equip_gear_btn = tk.Button(gear_button_frame, text="⚔️ Equip Selected Gear", 
                                  font=("Helvetica", 12), bg="#4CAF50", fg="white",
                                  command=lambda: self.equip_selected_gear_from_inventory(gear_listbox))
        equip_gear_btn.pack(side=tk.LEFT, padx=5)
        
        unequip_gear_btn = tk.Button(gear_button_frame, text="📤 Unequip Selected Gear", 
                                    font=("Helvetica", 12), bg="#FF9800", fg="white",
                                    command=lambda: self.unequip_selected_gear_from_inventory(gear_listbox))
        unequip_gear_btn.pack(side=tk.LEFT, padx=5)

        # Stats Tab
        stats_frame = tk.Frame(notebook, bg="#F0F8FF")
        notebook.add(stats_frame, text="📊 Stats")
    
        stats_label = tk.Label(stats_frame, text="Character Stats:", 
                          font=("Helvetica", 14, "bold"), bg="#F0F8FF")
        stats_label.pack(pady=5)
    
        total_stats = self.player.get_total_stats()
        fish_bonuses = self.player.get_fish_bonuses()
        
        # Show breakdown of bonuses
        gear_luck = total_stats['luck'] - self.player.base_luck - fish_bonuses['luck']
        gear_attack = total_stats['attack'] - self.player.base_attack - fish_bonuses['attack']
        gear_defense = total_stats['defense'] - self.player.base_defense - fish_bonuses['defense']
        gear_speed = total_stats['speed'] - self.player.base_speed - fish_bonuses['speed']
        
        stats_text = f"""Stats:
❤️ Health: {self.player.health}/{self.player.max_health}
💰 Gold: {self.player.gold}
⚡ Energy: {self.player.energy}
🎯 Level: {self.player.level}

🍀 Luck: {total_stats['luck']} (Base: {self.player.base_luck}"""
        if gear_luck > 0:
            stats_text += f" + {gear_luck} gear"
        if fish_bonuses['luck'] > 0:
            stats_text += f" + {fish_bonuses['luck']} fish"
        stats_text += ")\n"
        
        stats_text += f"""⚔️ Attack: {total_stats['attack']} (Base: {self.player.base_attack}"""
        if gear_attack > 0:
            stats_text += f" + {gear_attack} gear"
        if fish_bonuses['attack'] > 0:
            stats_text += f" + {fish_bonuses['attack']} fish"
        stats_text += ")\n"
        
        stats_text += f"""🛡️ Defense: {total_stats['defense']} (Base: {self.player.base_defense}"""
        if gear_defense > 0:
            stats_text += f" + {gear_defense} gear"
        if fish_bonuses['defense'] > 0:
            stats_text += f" + {fish_bonuses['defense']} fish"
        stats_text += ")\n"
        
        stats_text += f"""💨 Speed: {total_stats['speed']} (Base: {self.player.base_speed}"""
        if gear_speed > 0:
            stats_text += f" + {gear_speed} gear"
        if fish_bonuses['speed'] > 0:
            stats_text += f" + {fish_bonuses['speed']} fish"
        stats_text += ")\n\n"
        
        stats_text += f"""Inventory Count:
🐟 Fish: {fish_count}
📦 Items: {item_count}
⚔️ Gear: {len(self.player.gear_inventory)}"""
        
        stats_display = tk.Label(stats_frame, text=stats_text, 
                            font=("Helvetica", 11), bg="#F0F8FF", 
                            justify=tk.LEFT, anchor="nw")
        stats_display.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
        # Close button
        close_btn = tk.Button(self.inventory_window, text="Close", 
                         font=("Helvetica", 12), command=self.inventory_window.destroy)
        close_btn.pack(pady=10)

    def equip_selected_gear_from_inventory(self, gear_listbox):
        """Equip selected gear from the inventory window"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        selection = gear_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select gear to equip!")
            return
        
        # Get gear from inventory
        if not self.player.gear_inventory:
            messagebox.showinfo("No Gear", "No gear available to equip!")
            return
        
        selected_index = selection[0]
        if selected_index >= len(self.player.gear_inventory):
            messagebox.showwarning("Invalid Selection", "Selected gear not found!")
            return
        
        selected_gear = self.player.gear_inventory[selected_index]
        
        if selected_gear.equipped:
            messagebox.showinfo("Already Equipped", f"{selected_gear.name} is already equipped!")
            return
        
        # Equip the gear
        self.player.equip_gear(selected_gear)
        
        # Log the equipment change
        bonus_text = ""
        if selected_gear.stat_bonus:
            bonus_list = [f"+{value} {stat}" for stat, value in selected_gear.stat_bonus.items()]
            bonus_text = f" ({', '.join(bonus_list)})"
        self.log_message(f"⚔️ Equipped {selected_gear.name}{bonus_text}!")
        
        # Update displays
        self.update_player_info()
        
        # Refresh the inventory window
        self.inventory_window.destroy()
        self.open_inventory_window()
        
        # Show success message
        messagebox.showinfo("Gear Equipped", f"Equipped {selected_gear.name}!")

    def unequip_selected_gear_from_inventory(self, gear_listbox):
        """Unequip selected gear from the inventory window"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        selection = gear_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select gear to unequip!")
            return
        
        # Get gear from inventory
        if not self.player.gear_inventory:
            messagebox.showinfo("No Gear", "No gear available to unequip!")
            return
        
        selected_index = selection[0]
        if selected_index >= len(self.player.gear_inventory):
            messagebox.showwarning("Invalid Selection", "Selected gear not found!")
            return
        
        selected_gear = self.player.gear_inventory[selected_index]
        
        if not selected_gear.equipped:
            messagebox.showinfo("Not Equipped", f"{selected_gear.name} is not equipped!")
            return
        
        # Unequip the gear
        selected_gear.equipped = False
        
        # Remove from equipment slot
        if selected_gear.gear_type == "rod":
            self.player.equipped_rod = None
        elif selected_gear.gear_type == "head":
            self.player.equipped_head = None
        elif selected_gear.gear_type == "torso":
            self.player.equipped_torso = None
        elif selected_gear.gear_type == "leg":
            self.player.equipped_leg = None
        elif selected_gear.gear_type == "foot":
            self.player.equipped_foot = None
        elif selected_gear.gear_type == "glove":
            self.player.equipped_glove = None
        elif selected_gear.gear_type == "necklace":
            self.player.equipped_necklace = None
        elif selected_gear.gear_type == "ring":
            self.player.equipped_ring = None
        elif selected_gear.gear_type == "knife":
            self.player.equipped_knife = None
        
        # Log the equipment change
        self.log_message(f"📤 Unequipped {selected_gear.name}")
        
        # Update displays
        self.update_player_info()
        
        # Refresh the inventory window
        self.inventory_window.destroy()
        self.open_inventory_window()
        
        # Show success message
        messagebox.showinfo("Gear Unequipped", f"Unequipped {selected_gear.name}!")

    def eat_selected_fish(self, fish_listbox):
        """Eat the selected fish from the inventory window"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        selection = fish_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a fish to eat!")
            return
        
        # Get fish from inventory (only fish items)
        fish_items = [item for item in self.player.inventory if hasattr(item, 'actual_size')]
        
        if not fish_items:
            messagebox.showinfo("No Fish", "No fish available to eat!")
            return
        
        selected_index = selection[0]
        if selected_index >= len(fish_items):
            messagebox.showwarning("Invalid Selection", "Selected fish not found!")
            return
        
        selected_fish = fish_items[selected_index]
        
        # Check if player is at max energy
        if self.player.energy >= self.player.max_energy:
            confirm = messagebox.askyesno("Already Full Energy", 
                                         f"You're already at max energy ({self.player.max_energy}).\nEat {selected_fish.name} anyway?")
            if not confirm:
                return
        
        # Eat the fish
        result = self.player.eat_fish(selected_fish)
        self.log_message(result)
        
        # Update displays
        self.update_player_info()
        
        # Refresh the inventory window
        self.inventory_window.destroy()
        self.open_inventory_window()
        
        # Show success message
        messagebox.showinfo("Fish Eaten", f"Ate {selected_fish.name} and restored {selected_fish.food_value} energy!")

    def open_gear_window(self):
        """Open gear management window"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # Create new window
        self.gear_window = tk.Toplevel(self.root)
        self.gear_window.title(f"{self.player.name}'s Equipment")
        self.gear_window.geometry("900x700")
        self.gear_window.configure(bg="#F0F8FF")

        title_label = tk.Label(self.gear_window, text=f"⚔️ {self.player.name}'s Equipment", 
                          font=("Helvetica", 18, "bold"), bg="#F0F8FF")
        title_label.pack(pady=10)

        main_container = tk.Frame(self.gear_window, bg="#F0F8FF")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Left side - Equipment Slots
        left_frame = tk.Frame(main_container, bg="#E6F3FF", relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        equipped_label = tk.Label(left_frame, text="📦 Equipped Gear", 
                             font=("Helvetica", 14, "bold"), bg="#E6F3FF")
        equipped_label.pack(pady=10)

        slots_frame = tk.Frame(left_frame, bg="#E6F3FF")
        slots_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        equipment_slots = [
            ("🎣 Rod", self.player.equipped_rod, "rod"),
            ("🎩 Head", self.player.equipped_head, "head"),
            ("👕 Torso", self.player.equipped_torso, "torso"),
            ("👖 Legs", self.player.equipped_leg, "leg"),
            ("👟 Feet", self.player.equipped_foot, "foot"),
            ("🧤 Gloves", self.player.equipped_glove, "glove"),
            ("📿 Necklace", self.player.equipped_necklace, "necklace"),
            ("💍 Ring", self.player.equipped_ring, "ring"),
            ("🔪 Knife", self.player.equipped_knife, "knife")
        ]

        self.slot_labels = {}  # Store references for updating

        for i, (slot_name, equipped_item, slot_type) in enumerate(equipment_slots):
            slot_frame = tk.Frame(slots_frame, bg="#E6F3FF")
            slot_frame.pack(fill=tk.X, pady=2)

        # Slot name
            name_label = tk.Label(slot_frame, text=slot_name, 
                             font=("Helvetica", 12, "bold"), bg="#E6F3FF", width=12, anchor="w")
            name_label.pack(side=tk.LEFT)

        # Equipped item info
            if equipped_item:
                bonus_text = ""
                if equipped_item.stat_bonus:
                    bonus_list = [f"+{value} {stat}" for stat, value in equipped_item.stat_bonus.items()]
                    bonus_text = f" ({', '.join(bonus_list)})"
                item_text = f"{equipped_item.name}{bonus_text}"
                bg_color = "#90EE90"  # Light green for equipped
            else:
                item_text = "Empty"
                bg_color = "#FFE4E1"  # Light pink for empty

            item_label = tk.Label(slot_frame, text=item_text, 
                             font=("Helvetica", 10), bg=bg_color, 
                             relief=tk.SUNKEN, bd=1, anchor="w")
            item_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Store reference for updating
            self.slot_labels[slot_type] = item_label

    # Stats display
        stats_frame = tk.Frame(left_frame, bg="#E6F3FF")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        stats_label = tk.Label(stats_frame, text="📊 Current Stats", 
                          font=("Helvetica", 12, "bold"), bg="#E6F3FF")
        stats_label.pack()

        total_stats = self.player.get_total_stats()
        stats_text = f"""🍀 Luck: {total_stats['luck']} (Base: {self.player.base_luck})
⚔️ Attack: {total_stats['attack']} (Base: {self.player.base_attack})
🛡️ Defense: {total_stats['defense']} (Base: {self.player.base_defense})
💨 Speed: {total_stats['speed']} (Base: {self.player.base_speed})
        """

        self.gear_stats_display = tk.Label(stats_frame, text=stats_text, 
                                      font=("Helvetica", 10), bg="#E6F3FF", 
                                      justify=tk.LEFT, anchor="nw")
        self.gear_stats_display.pack(fill=tk.X, pady=5)

        # Right side - Available Gear
        right_frame = tk.Frame(main_container, bg="#FFE6E6", relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        inventory_label = tk.Label(right_frame, text="🎒 Gear Inventory", 
                              font=("Helvetica", 14, "bold"), bg="#FFE6E6")
        inventory_label.pack(pady=10)

    # Instructions
        instruction_label = tk.Label(right_frame, text="Select gear and click Equip/Unequip", 
                                font=("Helvetica", 10), bg="#FFE6E6", fg="gray")
        instruction_label.pack(pady=2)

    # Gear listbox with scrollbar
        listbox_frame = tk.Frame(right_frame, bg="#FFE6E6")
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.gear_listbox = tk.Listbox(listbox_frame, font=("Helvetica", 10), 
                               yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
        self.gear_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.gear_listbox.yview)

    # Populate gear list
        self.refresh_gear_list()

        # Gear action buttons (updated for batch operations)
        button_frame = tk.Frame(right_frame, bg="#FFE6E6")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        # First row of buttons
        button_row1 = tk.Frame(button_frame, bg="#FFE6E6")
        button_row1.pack(fill=tk.X, pady=2)

        equip_btn = tk.Button(button_row1, text="⚔️ Equip Selected", 
                     font=("Helvetica", 11), bg="#4CAF50", fg="white",
                     command=self.equip_multiple_gear)
        equip_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        unequip_btn = tk.Button(button_row1, text="📤 Unequip Selected", 
                       font=("Helvetica", 11), bg="#FF9800", fg="white",
                       command=self.unequip_multiple_gear)
        unequip_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Second row of buttons
        button_row2 = tk.Frame(button_frame, bg="#FFE6E6")
        button_row2.pack(fill=tk.X, pady=2)

        select_all_btn = tk.Button(button_row2, text="📋 Select All", 
                          font=("Helvetica", 11), bg="#2196F3", fg="white",
                          command=self.select_all_gear)
        select_all_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        clear_selection_btn = tk.Button(button_row2, text="🚫 Clear Selection", 
                               font=("Helvetica", 11), bg="#757575", fg="white",
                               command=self.clear_gear_selection)
        clear_selection_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Third row - Batch operations
        button_row3 = tk.Frame(button_frame, bg="#FFE6E6")
        button_row3.pack(fill=tk.X, pady=2)

        equip_all_btn = tk.Button(button_row3, text="⚔️ Equip All Unequipped", 
                         font=("Helvetica", 11), bg="#27AE60", fg="white",
                         command=self.equip_all_unequipped_gear)
        equip_all_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        unequip_all_btn = tk.Button(button_row3, text="📤 Unequip All", 
                           font=("Helvetica", 11), bg="#E74C3C", fg="white",
                           command=self.unequip_all_gear)
        unequip_all_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Close button
        close_btn = tk.Button(self.gear_window, text="Close", 
                     font=("Helvetica", 12), bg="#757575", fg="white",
                     command=self.gear_window.destroy)
        close_btn.pack(pady=10)

    def select_all_gear(self):
        """Select all gear items in the listbox"""
        if hasattr(self, 'gear_listbox'):
            self.gear_listbox.select_set(0, tk.END)

    def clear_gear_selection(self):
        """Clear all selections in the gear listbox"""
        if hasattr(self, 'gear_listbox'):
            self.gear_listbox.selection_clear(0, tk.END)

    def equip_multiple_gear(self):
        """Equip all selected gear items"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        selections = self.gear_listbox.curselection()
        
        if not selections:
            messagebox.showwarning("No Selection", "Please select gear to equip!")
            return
        
        equipped_count = 0
        already_equipped = 0
        equipped_items = []
        
        for gear_index in selections:
            if gear_index >= len(self.player.gear_inventory):
                continue
            
            selected_gear = self.player.gear_inventory[gear_index]
            
            if selected_gear.equipped:
                already_equipped += 1
                continue
            
            # Equip the gear
            self.player.equip_gear(selected_gear)
            equipped_count += 1
            equipped_items.append(selected_gear.name)
        
        # Show results
        if equipped_count > 0:
            items_text = ", ".join(equipped_items[:3])  # Show first 3 items
            if len(equipped_items) > 3:
                items_text += f" and {len(equipped_items) - 3} more"
            
            self.log_message(f"⚔️ Equipped {equipped_count} items: {items_text}")
            
            if already_equipped > 0:
                messagebox.showinfo("Batch Equip Complete", 
                                f"Equipped {equipped_count} items!\n{already_equipped} items were already equipped.")
            else:
                messagebox.showinfo("Batch Equip Complete", f"Successfully equipped {equipped_count} items!")
        else:
            if already_equipped > 0:
                messagebox.showinfo("Nothing to Equip", "All selected items are already equipped!")
            else:
                messagebox.showwarning("No Valid Gear", "No valid gear selected to equip!")
        
        # Refresh displays
        self.refresh_gear_window()
        self.update_player_info()

    def unequip_multiple_gear(self):
        """Unequip all selected gear items"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        selections = self.gear_listbox.curselection()
        
        if not selections:
            messagebox.showwarning("No Selection", "Please select gear to unequip!")
            return
        
        unequipped_count = 0
        not_equipped = 0
        unequipped_items = []
        
        for gear_index in selections:
            if gear_index >= len(self.player.gear_inventory):
                continue
            
            selected_gear = self.player.gear_inventory[gear_index]
            
            if not selected_gear.equipped:
                not_equipped += 1
                continue
            
            # Unequip the gear
            selected_gear.equipped = False
            
            # Remove from equipment slot
            if selected_gear.gear_type == "rod":
                self.player.equipped_rod = None
            elif selected_gear.gear_type == "head":
                self.player.equipped_head = None
            elif selected_gear.gear_type == "torso":
                self.player.equipped_torso = None
            elif selected_gear.gear_type == "leg":
                self.player.equipped_leg = None
            elif selected_gear.gear_type == "foot":
                self.player.equipped_foot = None
            elif selected_gear.gear_type == "glove":
                self.player.equipped_glove = None
            elif selected_gear.gear_type == "necklace":
                self.player.equipped_necklace = None
            elif selected_gear.gear_type == "ring":
                self.player.equipped_ring = None
            elif selected_gear.gear_type == "knife":
                self.player.equipped_knife = None
            
            unequipped_count += 1
            unequipped_items.append(selected_gear.name)
        
        # Show results
        if unequipped_count > 0:
            items_text = ", ".join(unequipped_items[:3])  # Show first 3 items
            if len(unequipped_items) > 3:
                items_text += f" and {len(unequipped_items) - 3} more"
            
            self.log_message(f"📤 Unequipped {unequipped_count} items: {items_text}")
            
            if not_equipped > 0:
                messagebox.showinfo("Batch Unequip Complete", 
                                f"Unequipped {unequipped_count} items!\n{not_equipped} items were not equipped.")
            else:
                messagebox.showinfo("Batch Unequip Complete", f"Successfully unequipped {unequipped_count} items!")
        else:
            if not_equipped > 0:
                messagebox.showinfo("Nothing to Unequip", "None of the selected items are equipped!")
            else:
                messagebox.showwarning("No Valid Gear", "No valid gear selected to unequip!")
        
        # Refresh displays
        self.refresh_gear_window()
        self.update_player_info()

    def equip_all_unequipped_gear(self):
        """Equip all unequipped gear in inventory"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # Find all unequipped gear
        unequipped_gear = [gear for gear in self.player.gear_inventory if not gear.equipped]
        
        if not unequipped_gear:
            messagebox.showinfo("All Equipped", "All gear is already equipped!")
            return
        
        # Confirm batch equip
        confirm = messagebox.askyesno("Equip All Unequipped", 
                                    f"Equip all {len(unequipped_gear)} unequipped gear items?\n\n"
                                    "This will replace currently equipped items of the same type.")
        if not confirm:
            return
        
        equipped_count = 0
        equipped_items = []
        
        for gear in unequipped_gear:
            self.player.equip_gear(gear)
            equipped_count += 1
            equipped_items.append(gear.name)
        
        # Show results
        items_text = ", ".join(equipped_items[:5])  # Show first 5 items
        if len(equipped_items) > 5:
            items_text += f" and {len(equipped_items) - 5} more"
        
        self.log_message(f"⚔️ MASS EQUIP: Equipped {equipped_count} items: {items_text}")
        messagebox.showinfo("Mass Equip Complete", f"Successfully equipped all {equipped_count} unequipped items!")
        
        # Refresh displays
        self.refresh_gear_window()
        self.update_player_info()

    def unequip_all_gear(self):
        """Unequip all equipped gear"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        # Find all equipped gear
        equipped_gear = [gear for gear in self.player.gear_inventory if gear.equipped]
        
        if not equipped_gear:
            messagebox.showinfo("Nothing Equipped", "No gear is currently equipped!")
            return
        
        # Confirm batch unequip
        confirm = messagebox.askyesno("Unequip All Gear", 
                                    f"Unequip all {len(equipped_gear)} equipped gear items?")
        if not confirm:
            return
        
        unequipped_count = 0
        unequipped_items = []
        
        for gear in equipped_gear:
            gear.equipped = False
            unequipped_count += 1
            unequipped_items.append(gear.name)
        
        # Clear all equipment slots
        self.player.equipped_rod = None
        self.player.equipped_head = None
        self.player.equipped_torso = None
        self.player.equipped_leg = None
        self.player.equipped_foot = None
        self.player.equipped_glove = None
        self.player.equipped_necklace = None
        self.player.equipped_ring = None
        self.player.equipped_knife = None
        
        # Show results
        items_text = ", ".join(unequipped_items[:5])  # Show first 5 items
        if len(unequipped_items) > 5:
            items_text += f" and {len(unequipped_items) - 5} more"
        
        self.log_message(f"📤 MASS UNEQUIP: Unequipped {unequipped_count} items: {items_text}")
        messagebox.showinfo("Mass Unequip Complete", f"Successfully unequipped all {unequipped_count} equipped items!")
        
        # Refresh displays
        self.refresh_gear_window()
        self.update_player_info()

    def refresh_gear_list(self):
            """Refresh the gear inventory listbox"""
            if not hasattr(self, 'player') or self.player is None:
                return
            self.gear_listbox.delete(0, tk.END)
        
            if not self.player.gear_inventory:
                self.gear_listbox.insert(tk.END, "No gear in inventory")
                return
        
            for i, gear in enumerate(self.player.gear_inventory):
                equipped_text = " [EQUIPPED]" if gear.equipped else ""
                bonus_text = ""
                if gear.stat_bonus:
                    bonus_list = [f"+{value} {stat}" for stat, value in gear.stat_bonus.items()]
                    bonus_text = f" ({', '.join(bonus_list)})"
            
                display_text = f"{gear.name} [{gear.gear_type}]{bonus_text}{equipped_text}"
                self.gear_listbox.insert(tk.END, display_text)

    def equip_selected_gear(self):
            """Equip the selected gear"""
            if not hasattr(self, 'player') or self.player is None:
                return
            selection = self.gear_listbox.curselection()
        
            if not selection:
                messagebox.showwarning("No Selection", "Please select gear to equip!")
                return
        
            gear_index = selection[0]
            if gear_index >= len(self.player.gear_inventory):
                return
        
            selected_gear = self.player.gear_inventory[gear_index]
        
            if selected_gear.equipped:
                messagebox.showinfo("Already Equipped", f"{selected_gear.name} is already equipped!")
                return
        
        # Equip the gear
            self.player.equip_gear(selected_gear)
        
        # Refresh displays
            self.refresh_gear_window()
            self.update_player_info()
        
        # Log the equipment change
            bonus_text = ""
            if selected_gear.stat_bonus:
                bonus_list = [f"+{value} {stat}" for stat, value in selected_gear.stat_bonus.items()]
                bonus_text = f" ({', '.join(bonus_list)})"
            self.log_message(f"⚔️ Equipped {selected_gear.name}{bonus_text}!")
        
    def unequip_selected_gear(self):
            """Unequip the selected gear"""
            if not hasattr(self, 'player') or self.player is None:
                return
            selection = self.gear_listbox.curselection()
        
            if not selection:
                messagebox.showwarning("No Selection", "Please select gear to unequip!")
                return
        
            gear_index = selection[0]
            if gear_index >= len(self.player.gear_inventory):
                return
        
            selected_gear = self.player.gear_inventory[gear_index]
        
            if not selected_gear.equipped:
                messagebox.showinfo("Not Equipped", f"{selected_gear.name} is not equipped!")
                return
        
        # Unequip the gear
            selected_gear.equipped = False
        
        # Remove from equipment slot
            if selected_gear.gear_type == "rod":
                self.player.equipped_rod = None
            elif selected_gear.gear_type == "head":
                self.player.equipped_head = None
            elif selected_gear.gear_type == "torso":
                self.player.equipped_torso = None
            elif selected_gear.gear_type == "leg":
                self.player.equipped_leg = None
            elif selected_gear.gear_type == "foot":
                self.player.equipped_foot = None
            elif selected_gear.gear_type == "glove":
                self.player.equipped_glove = None
            elif selected_gear.gear_type == "necklace":
                self.player.equipped_necklace = None
            elif selected_gear.gear_type == "ring":
                self.player.equipped_ring = None
            elif selected_gear.gear_type == "knife":
                self.player.equipped_knife = None
        
        # Refresh displays
            self.refresh_gear_window()
            self.update_player_info()
        
        # Log the equipment change
            self.log_message(f"📤 Unequipped {selected_gear.name}")
        
    def refresh_gear_window(self):
            """Refresh all elements in the gear window"""
            if not hasattr(self, 'player') or self.player is None:
                return

            if not hasattr(self, 'gear_window') or not self.gear_window.winfo_exists():
                return
        
            # Refresh gear list
            self.refresh_gear_list()
        
            # Update equipment slots
            equipment_slots = [
                ("rod", self.player.equipped_rod),
                ("head", self.player.equipped_head),
                ("torso", self.player.equipped_torso),
                ("leg", self.player.equipped_leg),
                ("foot", self.player.equipped_foot),
                ("glove", self.player.equipped_glove),
                ("necklace", self.player.equipped_necklace),
                ("ring", self.player.equipped_ring),
                ("knife", self.player.equipped_knife)
            ]
            
            for slot_type, equipped_item in equipment_slots:
                if slot_type in self.slot_labels:
                    if equipped_item:
                        bonus_text = ""
                        if equipped_item.stat_bonus:
                            bonus_list = [f"+{value} {stat}" for stat, value in equipped_item.stat_bonus.items()]
                            bonus_text = f" ({', '.join(bonus_list)})"
                        item_text = f"{equipped_item.name}{bonus_text}"
                        bg_color = "#90EE90"  # Light green for equipped
                    else:
                        item_text = "Empty"
                        bg_color = "#FFE4E1"  # Light pink for empty
                    
                    self.slot_labels[slot_type].config(text=item_text, bg=bg_color)
            
            # Update stats display with fish bonuses
            total_stats = self.player.get_total_stats()
            fish_bonuses = self.player.get_fish_bonuses()
            
            # Show breakdown of bonuses
            gear_luck = total_stats['luck'] - self.player.base_luck - fish_bonuses['luck']
            gear_attack = total_stats['attack'] - self.player.base_attack - fish_bonuses['attack']
            gear_defense = total_stats['defense'] - self.player.base_defense - fish_bonuses['defense']
            gear_speed = total_stats['speed'] - self.player.base_speed - fish_bonuses['speed']
            
            stats_text = f"""🍀 Luck: {total_stats['luck']} (Base: {self.player.base_luck}"""
            if gear_luck > 0:
                stats_text += f" + {gear_luck} gear"
            if fish_bonuses['luck'] > 0:
                stats_text += f" + {fish_bonuses['luck']} fish"
            stats_text += ")\n"
            
            stats_text += f"""⚔️ Attack: {total_stats['attack']} (Base: {self.player.base_attack}"""
            if gear_attack > 0:
                stats_text += f" + {gear_attack} gear"
            if fish_bonuses['attack'] > 0:
                stats_text += f" + {fish_bonuses['attack']} fish"
            stats_text += ")\n"
            
            stats_text += f"""🛡️ Defense: {total_stats['defense']} (Base: {self.player.base_defense}"""
            if gear_defense > 0:
                stats_text += f" + {gear_defense} gear"
            if fish_bonuses['defense'] > 0:
                stats_text += f" + {fish_bonuses['defense']} fish"
            stats_text += ")\n"
            
            stats_text += f"""💨 Speed: {total_stats['speed']} (Base: {self.player.base_speed}"""
            if gear_speed > 0:
                stats_text += f" + {gear_speed} gear"
            if fish_bonuses['speed'] > 0:
                stats_text += f" + {fish_bonuses['speed']} fish"
            stats_text += ")\n"
            
            # Custom Text Here
            stats_text += f"""
    """
            
            
            self.gear_stats_display.config(text=stats_text)

    def open_items_window(self):
        """Open items window to use consumable items"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
       # Prevent multiple items windows
        if hasattr(self, 'items_window') and self.items_window.winfo_exists():
            self.items_window.lift()  # Bring existing window to front
            return

        # Get consumable items
        consumable_items = [item for item in self.player.inventory if hasattr(item, 'item_type') and item.item_type == "consumable"]
        
        if not consumable_items:
            messagebox.showinfo("No Items", "You don't have any consumable items!")
            return

       # Disable items button temporarily
        if hasattr(self, 'items_btn'):
            self.items_btn.config(state=tk.DISABLED)
            self.root.after(1000, lambda: self.items_btn.config(state=tk.NORMAL))        

        # Create new window
        self.items_window = tk.Toplevel(self.root)
        self.items_window.title("Use Items")
        self.items_window.geometry("600x500")
        self.items_window.configure(bg="#F5F5DC")
        
        # Window title
        title_label = tk.Label(self.items_window, text="🧪 Use Consumable Items", 
                              font=("Helvetica", 18, "bold"), bg="#F5F5DC")
        title_label.pack(pady=10)
        
        # Current stats display
        info_frame = tk.Frame(self.items_window, bg="#F5F5DC")
        info_frame.pack(pady=5)
        
        stats = self.player.get_total_stats()
        stats_text = f"❤️ Health: {self.player.health}/{self.player.max_health} | ⚡ Energy: {self.player.energy}/{self.player.max_energy} | 🍀 Luck: {stats['luck']} | ⚔️ Attack: {stats['attack']} | 🛡️ Defense: {stats['defense']} | 💨 Speed: {stats['speed']}"
        
        stats_label = tk.Label(info_frame, text=stats_text, 
                             font=("Helvetica", 10), bg="#F5F5DC", fg="blue")
        stats_label.pack(pady=5)
        
        # Items list
        items_label = tk.Label(self.items_window, text="Select an item to use:", 
                              font=("Helvetica", 12, "bold"), bg="#F5F5DC")
        items_label.pack(pady=(10, 5))
        
        # Frame for listbox and scrollbar
        listbox_frame = tk.Frame(self.items_window, bg="#F5F5DC")
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Listbox with scrollbar
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.items_listbox = tk.Listbox(listbox_frame, font=("Helvetica", 11), 
                                       yscrollcommand=scrollbar.set)
        self.items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.items_listbox.yview)
        
        # Store items for reference
        self.current_consumable_items = []
        
        # Add consumable items to list
        for item in consumable_items:
            display_text = f"🧪 {item.name} - {item.effect}"
            self.items_listbox.insert(tk.END, display_text)
            self.current_consumable_items.append(item)
        
        # Buttons frame
        button_frame = tk.Frame(self.items_window, bg="#F5F5DC")
        button_frame.pack(pady=20)
        
        # Use item button
        use_button = tk.Button(button_frame, text="✨ Use Selected Item", 
                              font=("Helvetica", 12), bg="#4CAF50", fg="white",
                              command=self.use_selected_item)
        use_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = tk.Button(button_frame, text="Close", 
                                font=("Helvetica", 12), bg="#757575", fg="white",
                                command=self.items_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

    def open_eat_fish_window(self):
        """Open eat fish window to consume fish for energy"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
       # Prevent multiple eat fish windows
        if hasattr(self, 'eat_fish_window') and self.eat_fish_window.winfo_exists():
            self.eat_fish_window.lift()  # Bring existing window to front
            return

        # Get fish from inventory
        fish_items = [item for item in self.player.inventory if hasattr(item, 'actual_size')]
        
        if not fish_items:
            messagebox.showinfo("No Fish", "You don't have any fish to eat!")
            return
        
       # Disable eat fish button temporarily
        if hasattr(self, 'eat_fish_btn'):
            self.eat_fish_btn.config(state=tk.DISABLED)
            self.root.after(1000, lambda: self.eat_fish_btn.config(state=tk.NORMAL))

        # Create new window
        self.eat_fish_window = tk.Toplevel(self.root)
        self.eat_fish_window.title("Eat Fish for Energy")
        self.eat_fish_window.geometry("700x600")
        self.eat_fish_window.configure(bg="#FFF8DC")
        
        # Window title
        title_label = tk.Label(self.eat_fish_window, text="🍽️ Eat Fish for Energy", 
                            font=("Helvetica", 18, "bold"), bg="#FFF8DC")
        title_label.pack(pady=10)
        
        # Current energy display
        info_frame = tk.Frame(self.eat_fish_window, bg="#FFF8DC")
        info_frame.pack(pady=5)
        
        energy_label = tk.Label(info_frame, text=f"Current Energy: {self.player.energy}", 
                            font=("Helvetica", 14), bg="#FFF8DC", fg="blue")
        energy_label.pack()
        
        # Energy warning if at max
        if self.player.energy >= self.player.max_energy:
            warning_label = tk.Label(info_frame, text="⚠️ You're at max energy! Eating won't restore more.", 
                                font=("Helvetica", 11), bg="#FFF8DC", fg="orange")
            warning_label.pack(pady=2)
        
        # Instructions
        instruction_label = tk.Label(self.eat_fish_window, text="Select fish to eat (multiple selection allowed):", 
                                    font=("Helvetica", 12, "bold"), bg="#FFF8DC")
        instruction_label.pack(pady=(10, 5))
        
        # Frame for listbox and scrollbar
        listbox_frame = tk.Frame(self.eat_fish_window, bg="#FFF8DC")
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # Listbox with scrollbar (allow multiple selections)
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.eat_fish_listbox = tk.Listbox(listbox_frame, font=("Helvetica", 11), 
                                        yscrollcommand=scrollbar.set, selectmode=tk.MULTIPLE)
        self.eat_fish_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.eat_fish_listbox.yview)
        
        # Store fish for reference
        self.current_fish_items = []
        
        # Add fish to listbox with energy preview
        for fish in fish_items:
            # Calculate potential energy gain
            potential_energy_gain = min(fish.food_value, self.player.max_energy - self.player.energy)
            
            # Show fish effects if any
            effect_text = ""
            if hasattr(fish, 'fish_effect') and fish.fish_effect != "none":
                # Extract stat bonus from fish effect for display
                import re
                match = re.search(r'\+(\d+)\s+(defense|attack|luck|speed)', fish.fish_effect.lower())
                if match:
                    bonus_amount = match.group(1)
                    stat_type = match.group(2)
                    effect_text = f" [+{bonus_amount} {stat_type}]"

            # Get sell value
            sell_value = fish.get_sell_value()

            display_text = f"🐟 {fish.name} ({fish.actual_size}in) +{fish.food_value} energy ({sell_value}g){effect_text}"
            self.eat_fish_listbox.insert(tk.END, display_text)
            self.current_fish_items.append(fish)
        
        # Energy preview frame
        preview_frame = tk.Frame(self.eat_fish_window, bg="#E6F3FF", relief=tk.SUNKEN, bd=2)
        preview_frame.pack(fill=tk.X, padx=20, pady=10)
        
        preview_title = tk.Label(preview_frame, text="📊 Energy Preview:", 
                            font=("Helvetica", 12, "bold"), bg="#E6F3FF")
        preview_title.pack(pady=2)
        
        self.energy_preview_label = tk.Label(preview_frame, text="Select fish to see energy preview", 
                                            font=("Helvetica", 11), bg="#E6F3FF", fg="gray")
        self.energy_preview_label.pack(pady=2)
        
        # Bind selection change to update preview
        self.eat_fish_listbox.bind('<<ListboxSelect>>', self.update_energy_preview)
        
        # Buttons frame
        button_frame = tk.Frame(self.eat_fish_window, bg="#FFF8DC")
        button_frame.pack(pady=20)
        
        # Eat selected button
        eat_selected_button = tk.Button(button_frame, text="🍽️ Eat Selected Fish", 
                                    font=("Helvetica", 12), bg="#4CAF50", fg="white",
                                    command=self.eat_selected_fish_from_window)
        eat_selected_button.pack(side=tk.LEFT, padx=5)
        
        # Select all button
        select_all_button = tk.Button(button_frame, text="📋 Select All Fish", 
                                    font=("Helvetica", 12), bg="#2196F3", fg="white",
                                    command=self.select_all_fish)
        select_all_button.pack(side=tk.LEFT, padx=5)
        
        # Eat all button (for quick energy restoration)
        eat_all_button = tk.Button(button_frame, text="🔥 Eat All Fish", 
                                font=("Helvetica", 12), bg="#FF5722", fg="white",
                                command=self.eat_all_fish)
        eat_all_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = tk.Button(button_frame, text="Close", 
                                font=("Helvetica", 12), bg="#757575", fg="white",
                                command=self.eat_fish_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

    def update_energy_preview(self, event=None):
        """Update the energy preview based on selected fish"""
        if not hasattr(self, 'player') or not hasattr(self, 'eat_fish_listbox') or self.player is None:
            return
        
        selections = self.eat_fish_listbox.curselection()
        
        if not selections:
            self.energy_preview_label.config(text="Select fish to see energy preview", fg="gray")
            return
        
        total_energy_value = 0
        fish_count = len(selections)
        
        for index in selections:
            if index < len(self.current_fish_items):
                fish = self.current_fish_items[index]
                total_energy_value += fish.food_value
        
        # Calculate actual energy that would be gained
        current_energy = self.player.energy
        max_energy = self.player.max_energy
        actual_energy_gain = min(total_energy_value, max_energy - current_energy)
        energy_after = current_energy + actual_energy_gain
        
        # Create preview text
        if fish_count == 1:
            preview_text = f"Eating 1 fish: {current_energy} → {energy_after} energy (+{actual_energy_gain})"
        else:
            preview_text = f"Eating {fish_count} fish: {current_energy} → {energy_after} energy (+{actual_energy_gain})"
        
        # Add warning if some energy would be wasted
        if total_energy_value > actual_energy_gain:
            wasted_energy = total_energy_value - actual_energy_gain
            preview_text += f" [⚠️ {wasted_energy} energy wasted]"
            self.energy_preview_label.config(text=preview_text, fg="orange")
        else:
            self.energy_preview_label.config(text=preview_text, fg="green")

    def select_all_fish(self):
        """Select all fish in the eat fish listbox"""
        if hasattr(self, 'eat_fish_listbox'):
            self.eat_fish_listbox.select_set(0, tk.END)
            self.update_energy_preview()

    def eat_selected_fish_from_window(self):
        """Eat selected fish from the eat fish window"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        selections = self.eat_fish_listbox.curselection()
        
        if not selections:
            messagebox.showwarning("No Selection", "Please select fish to eat!")
            return
        
        # Calculate total energy and effects
        total_energy_gained = 0
        fish_to_eat = []
        lost_effects = []
        
        for index in selections:
            if index < len(self.current_fish_items):
                fish = self.current_fish_items[index]
                fish_to_eat.append(fish)
                
                # Check for lost stat effects
                if hasattr(fish, 'fish_effect') and fish.fish_effect != "none":
                    import re
                    match = re.search(r'\+(\d+)\s+(defense|attack|luck|speed)', fish.fish_effect.lower())
                    if match:
                        bonus_amount = match.group(1)
                        stat_type = match.group(2)
                        lost_effects.append(f"+{bonus_amount} {stat_type}")
        
        if not fish_to_eat:
            return
        
        # Calculate actual energy gain
        total_food_value = sum(fish.food_value for fish in fish_to_eat)
        actual_energy_gain = min(total_food_value, self.player.max_energy - self.player.energy)
        
        # Confirm eating with details
        fish_names = [fish.name for fish in fish_to_eat]
        fish_text = ", ".join(fish_names[:3])
        if len(fish_names) > 3:
            fish_text += f" and {len(fish_names) - 3} more"
        
        confirm_text = f"Eat {len(fish_to_eat)} fish: {fish_text}?\n\nWill gain {actual_energy_gain} energy"
        
        if lost_effects:
            effects_text = ", ".join(lost_effects[:3])
            if len(lost_effects) > 3:
                effects_text += f" and {len(lost_effects) - 3} more"
            confirm_text += f"\n⚠️ You will lose stat bonuses: {effects_text}"
        
        if total_food_value > actual_energy_gain:
            wasted = total_food_value - actual_energy_gain
            confirm_text += f"\n⚠️ {wasted} energy will be wasted (already at/near max)"
        
        confirm = messagebox.askyesno("Confirm Eating", confirm_text)
        if not confirm:
            return
        
        # Eat all selected fish
        eaten_fish = []
        for fish in fish_to_eat:
            if fish in self.player.inventory:
                old_energy = self.player.energy
                self.player.energy = min(self.player.max_energy, self.player.energy + fish.food_value)
                energy_gained = self.player.energy - old_energy
                
                self.player.inventory.remove(fish)
                eaten_fish.append((fish.name, energy_gained))
        
        # Log the results
        if len(eaten_fish) == 1:
            fish_name, energy = eaten_fish[0]
            self.log_message(f"🍽️ Ate {fish_name}! Gained {energy} energy")
        else:
            total_gained = sum(energy for _, energy in eaten_fish)
            self.log_message(f"🍽️ Ate {len(eaten_fish)} fish! Gained {total_gained} total energy")
            
            # Show individual fish if not too many
            if len(eaten_fish) <= 5:
                for fish_name, energy in eaten_fish:
                    self.log_message(f"   • {fish_name} (+{energy} energy)")
        
        # Update displays
        self.update_player_info()
        
        # Close and reopen window to refresh the list
        self.eat_fish_window.destroy()
        
        # Show success message
        messagebox.showinfo("Fish Eaten", f"Successfully ate {len(eaten_fish)} fish!\nGained {actual_energy_gain} energy total.")
        
        # Reopen window if there are still fish to eat
        remaining_fish = [item for item in self.player.inventory if hasattr(item, 'actual_size')]
        if remaining_fish:
            self.open_eat_fish_window()

    def eat_all_fish(self):
        """Eat all fish in inventory"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        if not self.current_fish_items:
            messagebox.showinfo("No Fish", "No fish available to eat!")
            return
        
        # Calculate totals
        total_food_value = sum(fish.food_value for fish in self.current_fish_items)
        actual_energy_gain = min(total_food_value, self.player.max_energy - self.player.energy)
        
        # Count fish with effects
        fish_with_effects = []
        for fish in self.current_fish_items:
            if hasattr(fish, 'fish_effect') and fish.fish_effect != "none":
                fish_with_effects.append(fish.name)
        
        # Confirm eating all
        confirm_text = f"Eat ALL {len(self.current_fish_items)} fish?\n\nWill gain {actual_energy_gain} energy"
        
        if fish_with_effects:
            effects_count = len(fish_with_effects)
            confirm_text += f"\n⚠️ You will lose stat bonuses from {effects_count} fish"
        
        if total_food_value > actual_energy_gain:
            wasted = total_food_value - actual_energy_gain
            confirm_text += f"\n⚠️ {wasted} energy will be wasted"
        
        confirm = messagebox.askyesno("Confirm Eat All", confirm_text)
        if not confirm:
            return
        
        # Eat all fish
        eaten_count = 0
        total_energy_gained = 0
        
        # Make a copy of the list to avoid modification during iteration
        fish_to_eat = self.current_fish_items.copy()
        
        for fish in fish_to_eat:
            if fish in self.player.inventory:
                old_energy = self.player.energy
                self.player.energy = min(self.player.max_energy, self.player.energy + fish.food_value)
                energy_gained = self.player.energy - old_energy
                
                self.player.inventory.remove(fish)
                eaten_count += 1
                total_energy_gained += energy_gained
        
        # Log the results
        self.log_message(f"🔥 ATE ALL FISH! Consumed {eaten_count} fish for {total_energy_gained} energy!")
        
        # Update displays
        self.update_player_info()
        
        # Close window
        self.eat_fish_window.destroy()
        
        # Show success message
        messagebox.showinfo("All Fish Eaten", f"Ate all {eaten_count} fish!\nGained {total_energy_gained} energy total.")

    def use_selected_item(self):
        """Use the selected item from the items window"""
        if not hasattr(self, 'player') or self.player is None:
            return
    
        selection = self.items_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to use!")
            return
        
        # Get the selected item
        selected_index = selection[0]
        if selected_index >= len(self.current_consumable_items):
            messagebox.showwarning("Invalid Selection", "Selected item not found!")
            return
        
        selected_item = self.current_consumable_items[selected_index]
        
        # Confirm item use
        confirm = messagebox.askyesno("Confirm Use", 
                                    f"Use {selected_item.name}?\n\nEffect: {selected_item.effect}")
        if not confirm:
            return
        
        # Use the item using your existing method
        result = self.use_consumable_item(selected_item)
        
        # Log the result
        self.log_message(f"🧪 Used {selected_item.name}! {result}")
        
        # Update displays
        self.update_player_info()
        
        # Close and reopen items window to refresh the list
        self.items_window.destroy()
        
        # Show success message
        messagebox.showinfo("Item Used", f"Used {selected_item.name}!\n\n{result}")
        
        # Reopen items window if there are still consumable items
        remaining_consumables = [item for item in self.player.inventory if hasattr(item, 'item_type') and item.item_type == "consumable"]
        if remaining_consumables:
            self.open_items_window()

    def use_consumable_item(self, item):
        """Use a consumable item with proper handling"""
        if not hasattr(self, 'player') or self.player is None:
            return "No player found!"
        
        if item.item_type == "consumable":
            import re
            
            # Handle bait items FIRST (FIXED - moved to correct position and improved detection)
            if ("catch rate" in item.effect.lower() or 
                "increased catch rate" in item.effect.lower() or
                "fishing" in item.effect.lower() or
                "bait" in item.name.lower()):
                
                # Extract number of catches from effect text
                catch_match = re.search(r'for the next (\d+) catches?', item.effect)
                if catch_match:
                    boost_amount = int(catch_match.group(1))
                else:
                    # Try to extract any number from the effect
                    number_match = re.search(r'(\d+)', item.effect)
                    if number_match:
                        boost_amount = int(number_match.group(1))
                    else:
                        boost_amount = 3  # Default to 3 if no number found
                
                # Initialize bait boost if it doesn't exist
                if not hasattr(self.player, 'bait_boost_remaining'):
                    self.player.bait_boost_remaining = 0
                
                self.player.bait_boost_remaining += boost_amount
                self.player.inventory.remove(item)
                return f"Used {item.name}! Increased catch rate for the next {boost_amount} fishing attempts!"
            
            # Handle stat increase items - now more flexible for any stat and amount
            elif "increase" in item.effect and "by" in item.effect:
                # Try to match "increase any skill/stat by X"
                any_stat_match = re.search(r'increase any (?:skill|stat) by (\d+)', item.effect)
                if any_stat_match:
                    increase_amount = int(any_stat_match.group(1))
                    return self.choose_stat_increase(item, increase_amount)
                
                # Try to match specific stats like "increase speed by 3"
                specific_stat_match = re.search(r'increase (luck|attack|defense|speed) by (\d+)', item.effect, re.IGNORECASE)
                if specific_stat_match:
                    stat_name = specific_stat_match.group(1).lower()
                    increase_amount = int(specific_stat_match.group(2))
                    
                    # Map stat names to player attributes
                    stat_mapping = {
                        'luck': ('base_luck', 'Luck'),
                        'attack': ('base_attack', 'Attack'),
                        'defense': ('base_defense', 'Defense'),
                        'speed': ('base_speed', 'Speed')
                    }
                    
                    if stat_name in stat_mapping:
                        stat_attr, display_name = stat_mapping[stat_name]
                        setattr(self.player, stat_attr, getattr(self.player, stat_attr) + increase_amount)
                        self.player.inventory.remove(item)
                        return f"{display_name} increased by {increase_amount}!"
                
                # Fallback for old format "increase any skill by 3" without number
                if "increase any skill" in item.effect:
                    return self.choose_stat_increase(item, 3)  # Default to 3 for legacy items
            
            elif "restore" in item.effect and "health" in item.effect:
                # Health restoration items
                health_match = re.search(r'restore (\d+) health', item.effect)
                if health_match:
                    heal_amount = int(health_match.group(1))
                    old_health = self.player.health
                    self.player.health = min(self.player.max_health, self.player.health + heal_amount)
                    actual_healing = self.player.health - old_health
                    self.player.inventory.remove(item)
                    return f"Restored {actual_healing} health!"
            
            elif "restore" in item.effect and "energy" in item.effect:
                # Energy restoration items
                energy_match = re.search(r'restore (\d+) energy', item.effect)
                if energy_match:
                    energy_amount = int(energy_match.group(1))
                    old_energy = self.player.energy
                    self.player.energy = min(self.player.max_energy, self.player.energy + energy_amount)
                    actual_energy = self.player.energy - old_energy
                    self.player.inventory.remove(item)
                    return f"Gained {actual_energy} energy!"
        
        return "Item cannot be used."

    def choose_stat_increase(self, item, increase_amount=3, title="Choose Stat to Increase"):
        """Let player choose which stat to increase - now reusable for any item"""
        if not hasattr(self, 'player') or self.player is None:
            return "No player found!"
        # Create a simple dialog for stat selection
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Choose Stat to Increase")
        choice_window.geometry("450x350")
        choice_window.configure(bg="#F5F5DC")
        choice_window.transient(self.root)
        choice_window.grab_set()
        
        # Dynamic title based on item
        item_emoji = "📜" if "scroll" in item.name.lower() else "✨"
        title_label = tk.Label(choice_window, text=f"{item_emoji} {item.name}", 
                              font=("Helvetica", 16, "bold"), bg="#F5F5DC")
        title_label.pack(pady=10)
        
        instruction_label = tk.Label(choice_window, text=f"Choose which stat to increase by {increase_amount}:", 
                                    font=("Helvetica", 12), bg="#F5F5DC")
        instruction_label.pack(pady=5)
        
        # Item description
        if hasattr(item, 'description') and item.description:
            desc_label = tk.Label(choice_window, text=f'"{item.description}"', 
                                 font=("Helvetica", 10, "italic"), bg="#F5F5DC", 
                                 fg="gray", wraplength=400)
            desc_label.pack(pady=5)
        
        # Current stats display with preview
        stats = self.player.get_total_stats()
        stats_text = f"🍀 Luck: {stats['luck']} → {stats['luck'] + increase_amount}\n⚔️ Attack: {stats['attack']} → {stats['attack'] + increase_amount}\n🛡️ Defense: {stats['defense']} → {stats['defense'] + increase_amount}\n💨 Speed: {stats['speed']} → {stats['speed'] + increase_amount}"
        
        current_stats_label = tk.Label(choice_window, text=stats_text, 
                                      font=("Helvetica", 10), bg="#F5F5DC", 
                                      justify=tk.LEFT)
        current_stats_label.pack(pady=10)
        
        # Buttons for each stat
        button_frame = tk.Frame(choice_window, bg="#F5F5DC")
        button_frame.pack(pady=20)
        
        result_text = [""]  # Use list to modify from inner functions
        
        def increase_stat(stat_name, stat_attr):
            if self.player is None:
                result_text[0] = "No player found!"
                choice_window.destroy()
                return

            setattr(self.player, stat_attr, getattr(self.player, stat_attr) + increase_amount)
            self.player.inventory.remove(item)
            result_text[0] = f"{stat_name} increased by {increase_amount}!"
            choice_window.destroy()
        
        # Color-coded stat buttons - now uses dynamic increase_amount
        luck_btn = tk.Button(button_frame, text=f"🍀 Increase Luck (+{increase_amount})", 
                            font=("Helvetica", 12), bg="#FFD700", fg="black",
                            command=lambda: increase_stat("Luck", "base_luck"))
        luck_btn.pack(pady=3, fill=tk.X)
        
        attack_btn = tk.Button(button_frame, text=f"⚔️ Increase Attack (+{increase_amount})", 
                              font=("Helvetica", 12), bg="#FF4444", fg="white",
                              command=lambda: increase_stat("Attack", "base_attack"))
        attack_btn.pack(pady=3, fill=tk.X)
        
        defense_btn = tk.Button(button_frame, text=f"🛡️ Increase Defense (+{increase_amount})", 
                               font=("Helvetica", 12), bg="#4444FF", fg="white",
                               command=lambda: increase_stat("Defense", "base_defense"))
        defense_btn.pack(pady=3, fill=tk.X)
        
        speed_btn = tk.Button(button_frame, text=f"💨 Increase Speed (+{increase_amount})", 
                             font=("Helvetica", 12), bg="#44FF44", fg="black",
                             command=lambda: increase_stat("Speed", "base_speed"))
        speed_btn.pack(pady=3, fill=tk.X)
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                              font=("Helvetica", 12), bg="#757575", fg="white",
                              command=choice_window.destroy)
        cancel_btn.pack(pady=(10, 0), fill=tk.X)
        
        # Wait for window to close
        self.root.wait_window(choice_window)
        
        return result_text[0] if result_text[0] else f"{item.name} use cancelled."

    def explore_interface(self):
        """Handle exploration - costs 1 energy and can trigger special events"""
        if hasattr(self, 'explore_btn'):
            self.explore_btn.config(state=tk.DISABLED)
        
        try:
            if not hasattr(self, 'player') or self.player is None:
                self.log_message("❌ No player found! Please start a new game.")
                return

            if self.player.health <= 0:
                self.log_message("💀 You cannot explore while defeated!")
                self.show_game_over_screen()
                return

            if not self.player.use_energy(1):
                self.log_message("❌ Not enough energy to explore!")
                return

            # UPDATE PLAYER INFO IMMEDIATELY AFTER USING ENERGY
            self.update_player_info()

            selected_location = self.location_var.get()
            
            # Initialize exploration counters if they don't exist
            if not hasattr(self.player, 'exploration_counts'):
                self.player.exploration_counts = {}
            
            # Increment exploration count for this location
            if selected_location not in self.player.exploration_counts:
                self.player.exploration_counts[selected_location] = 0
            self.player.exploration_counts[selected_location] += 1
            
            # Check for special encounters based on location and exploration count
            special_event_occurred = self.check_special_exploration_events(selected_location)
            
            if not special_event_occurred:
                # Regular exploration results
                result = self.regular_exploration(selected_location)
                self.log_message(f"🗺️ Exploring {selected_location}: {result}")

            # Check for newly unlocked locations after exploration
            self.check_and_unlock_locations()

            # Check for game over AFTER updating UI
            if self.player.health <= 0:
                self.log_message("💀 GAME OVER! You have been defeated!")
                self.root.after(1000, self.show_game_over_screen)
                return
            elif self.player.is_game_over():
                self.log_message("💀 GAME OVER! You ran out of energy!")
                self.root.after(1000, self.show_game_over_screen)
                return

            # Final update (in case anything changed during exploration)
            self.update_player_info()

        finally:
            if hasattr(self, 'explore_btn'):
                self.root.after(500, lambda: self.explore_btn.config(state=tk.NORMAL))

    def check_exploration_requirements(self, event):
        """Check if player meets requirements for an exploration event"""
        if not hasattr(self, 'player') or self.player is None:
            return False
        
        # Check if event has requirements
        requirements = event.get('requirements', {})
        if not requirements:
            return True  # No requirements means always available
        
        # Check level requirement
        if 'min_level' in requirements:
            if self.player.level < requirements['min_level']:
                return False
        
        # ADD THIS: Check has_item requirement
        if 'has_item' in requirements:
            required_item = requirements['has_item']
            player_has_item = False
            
            for item in self.player.inventory:
                if hasattr(item, 'name') and item.name == required_item:
                    player_has_item = True
                    break
            
            if not player_has_item:
                return False

        # ADD THIS: Check does_not_have_item requirement
        if 'does_not_have_item' in requirements:
            forbidden_item = requirements['does_not_have_item']
            player_has_forbidden_item = False
            
            for item in self.player.inventory:
                if hasattr(item, 'name') and item.name == forbidden_item:
                    player_has_forbidden_item = True
                    break
            
            if player_has_forbidden_item:
                return False  # Player has item they shouldn't have

        # ADD THIS: Check has_gear requirement
        if 'has_gear' in requirements:
            required_gear = requirements['has_gear']
            player_has_gear = False
            
            for gear in self.player.gear_inventory:
                if hasattr(gear, 'name') and gear.name == required_gear:
                    player_has_gear = True
                    break
            
            if not player_has_gear:
                return False
        
        # ADD THIS: Check does_not_have_gear requirement
        if 'does_not_have_gear' in requirements:
            forbidden_gear = requirements['does_not_have_gear']
            player_has_forbidden_gear = False
            
            for gear in self.player.gear_inventory:
                if hasattr(gear, 'name') and gear.name == forbidden_gear:
                    player_has_forbidden_gear = True
                    break
            
            if player_has_forbidden_gear:
                return False  # Player has gear they shouldn't have

        # Check exploration count requirement
        if 'min_explorations' in requirements:
            location_name = event.get('location', '')
            exploration_count = self.player.exploration_counts.get(location_name, 0)
            if exploration_count < requirements['min_explorations']:
                return False
        
        # FIXED: Check completed explorations requirement
        if 'completed_explorations' in requirements:
            required_explorations = requirements['completed_explorations']
            if not hasattr(self.player, 'completed_explorations'):
                self.player.completed_explorations = []
            
            # Check if ALL required explorations have been completed
            for required_exploration in required_explorations:
                if required_exploration not in self.player.completed_explorations:
                    return False  # Required exploration not completed yet
        
        # Check completed trades requirement
        if 'required_trades' in requirements:
            required_trades = requirements['required_trades']
            if not hasattr(self.player, 'completed_trades'):
                self.player.completed_trades = []
            
            for trade_name in required_trades:
                if trade_name not in self.player.completed_trades:
                    return False
        
        # Check gold requirement
        if 'min_gold' in requirements:
            if self.player.gold < requirements['min_gold']:
                return False
        
        # Check stats requirements
        if 'min_stats' in requirements:
            player_stats = self.player.get_total_stats()
            min_stats = requirements['min_stats']
            
            for stat_name, min_value in min_stats.items():
                if player_stats.get(stat_name, 0) < min_value:
                    return False
        
        return True

    def check_special_exploration_events(self, location_name):
        """Check for special exploration events based on location and exploration count"""
        if not hasattr(self, 'player') or self.player is None:
            return False
        
        # Check if we have exploration data loaded
        if not hasattr(self, 'exploration_data'):
            print("❌ No exploration data loaded")
            return False
        
        exploration_count = self.player.exploration_counts.get(location_name, 0)
        
        # Initialize completed explorations if not exists
        if not hasattr(self.player, 'completed_explorations'):
            self.player.completed_explorations = []
        
        # ADD DEBUG OUTPUT
        print(f"\n🔍 Checking exploration events for: {location_name}")
        print(f"   Exploration count: {exploration_count}")
        print(f"   Player completed explorations: {self.player.completed_explorations}")
        
        # Check location-specific exploration events
        if location_name in self.exploration_data.get('explorations', {}):
            available_events = self.exploration_data['explorations'][location_name]
            
            print(f"   Available events for location: {len(available_events)}")
            
            # Filter events that haven't been completed and meet requirements
            eligible_events = []
            for event in available_events:
                # SAFETY CHECK: Skip events without IDs
                if 'id' not in event:
                    print(f"⚠️ Skipping event without ID: {event}")
                    continue
                
                event_id = event['id']
                print(f"   Checking event: {event_id}")
                
                # Check if already completed
                if event_id in self.player.completed_explorations:
                    print(f"     ❌ Already completed")
                    continue
                
                # Check requirements
                requirements_met = self.check_exploration_requirements(event)
                print(f"     Requirements met: {requirements_met}")
                
                if requirements_met:
                    eligible_events.append(event)
                    print(f"     ✅ Event eligible")
                else:
                    print(f"     ❌ Requirements not met")
                    # Debug the specific requirements
                    requirements = event.get('requirements', {})
                    if 'completed_explorations' in requirements:
                        required = requirements['completed_explorations']
                        print(f"       Required: {required}")
                        print(f"       Player has: {self.player.completed_explorations}")
            
            print(f"   Total eligible events: {len(eligible_events)}")
            
            if eligible_events:
                selected_event = eligible_events[0]
                
                print(f"🎯 Selected event: {selected_event['id']}")
                
                # Mark as completed if not repeatable
                if not selected_event.get('repeatable', False):
                    self.player.completed_explorations.append(selected_event['id'])
                
                # Show the exploration event
                self.show_dialogue_window(selected_event)
                
                # Handle actions for ALL events
                self.handle_exploration_actions(selected_event)
                
                return True
        else:
            print(f"   ❌ No events defined for location: {location_name}")
        
        return False

    def trigger_exploration_event(self, event_name, event_data):
        """Trigger a specific exploration event"""
        event_type = event_data.get("type", "dialogue")
        
        if event_type == "dialogue":
            self.show_dialogue_window(event_data)
        # Add more event types here later if needed

    def handle_exploration_actions(self, exploration):
        """Handle actions from exploration events - standardized to use 'add_' format"""
        if 'actions' not in exploration:
            return

        actions = exploration['actions']

        # Handle location unlocking
        if 'unlock_location' in actions:
            location_name = actions['unlock_location']
            
            # Initialize unlocked locations if not exists
            if not hasattr(self.player, 'unlocked_locations'):
                self.player.unlocked_locations = []
            
            if location_name not in self.player.unlocked_locations:
                self.player.unlocked_locations.append(location_name)
                self.log_message(f"🗺️ New location unlocked: {location_name}")
                
                # Update the location dropdown immediately
                self.update_location_dropdown()

        # Handle adding gear (standardized name)
        if 'add_gear' in actions:
            gear_name = actions['add_gear']
            # Find gear in gear.json
            for gear_data in self.gear_data['gear']:
                if gear_data['name'] == gear_name:
                    gear_item = Gear(gear_data)
                    self.player.add_gear(gear_item)
                    self.log_message(f"🎁 You received: {gear_name}!")
                    break
            else:
                self.log_message(f"⚠️ Error: Gear '{gear_name}' not found!")

        # Handle adding items (standardized name) - using same logic as Trade class
        if 'add_item' in actions:
            items_to_add = actions['add_item']
            
            # Handle both single item and list of items
            if isinstance(items_to_add, list):
                for item_entry in items_to_add:
                    item_name = item_entry.get('name', '')
                    quantity = item_entry.get('quantity', 1)
                    
                    # Give the specified quantity using Trade class logic
                    for _ in range(quantity):
                        # Find item in items.json
                        item_found = False
                        for item_data in self.item_data['items']:
                            if item_data['name'] == item_name:
                                item = Item(item_data)
                                self.player.add_item(item)
                                item_found = True
                                break
                        
                        if not item_found:
                            self.log_message(f"⚠️ Error: Item '{item_name}' not found in items.json!")
                            break
                    
                    if item_found:
                        if quantity == 1:
                            self.log_message(f"🎁 You received: {item_name}!")
                        else:
                            self.log_message(f"🎁 You received: {quantity}x {item_name}!")
            else:
                # Handle single item (legacy support)
                item_name = items_to_add
                # Use Trade class logic for single items
                for item_data in self.item_data['items']:
                    if item_data['name'] == item_name:
                        item = Item(item_data)
                        self.player.add_item(item)
                        self.log_message(f"🎁 You received: {item_name}!")
                        break
                else:
                    self.log_message(f"⚠️ Error: Item '{item_name}' not found in items.json!")
        
        # FIXED: Properly handle remove_item action with better item matching
        if 'remove_item' in actions:
            item_name = actions['remove_item']
            
            # Find and remove the item from player inventory
            item_found = False
            for item in self.player.inventory[:]:  # Use slice copy to avoid modification issues
                # Check the item's name attribute directly
                item_obj_name = getattr(item, 'name', None)
                
                if item_obj_name == item_name:
                    self.player.inventory.remove(item)
                    self.log_message(f"📦 Used {item_name}")
                    item_found = True
                    break
            
            if not item_found:
                self.log_message(f"⚠️ Could not find {item_name} to remove!")

        # Update inventory display after adding/removing items
        self.update_player_info()

    def check_and_unlock_locations(self):
        """Check if any new locations should be unlocked and update the dropdown"""
        # This is called after exploration to check for any location unlocks
        # The actual unlocking happens in handle_exploration_actions
        self.update_location_dropdown()

    def update_location_dropdown(self):
        """Update the location dropdown with newly available locations"""
        if not hasattr(self, 'location_dropdown'):
            return
        
        # Get updated list of available locations
        available_locations = self.get_available_locations()
        
        # Update the dropdown values
        self.location_dropdown['values'] = available_locations
        
        # If current selection is not in the new list, reset to first available
        current_location = self.location_var.get()
        if current_location not in available_locations and available_locations:
            self.location_var.set(available_locations[0])

    def show_dialogue_window(self, event):
        """Show dialogue window with optional GIF for hermit encounters"""
        if not hasattr(self, 'player') or self.player is None:
            return

        # Create dialogue window
        dialogue_window = tk.Toplevel(self.root)
        dialogue_window.title(event.get('title', 'Dialogue'))
        dialogue_window.configure(bg="#2C3E50")
        dialogue_window.state('zoomed')
        
        # Make window modal
        dialogue_window.transient(self.root)
        dialogue_window.grab_set()

        # Check if this event has a GIF specified in JSON
        gif_path = event.get('gif_path', None)

        # Create main frame
        main_frame = tk.Frame(dialogue_window, bg="#2C3E50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Smaller title at the top
        title_label = tk.Label(main_frame, text=event.get('title', 'Dialogue'),
                            font=("Helvetica", 14, "bold"), fg="#ECF0F1", bg="#2C3E50")
        title_label.pack(pady=(0, 20))

        # Content frame with dialogue on left and GIF on right
        content_container = tk.Frame(main_frame, bg="#2C3E50")
        content_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Left side - Dialogue text
        dialogue_frame = tk.Frame(content_container, bg="#34495E", relief=tk.RAISED, bd=2)
        dialogue_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        # Scrollable text area
        text_widget = tk.Text(dialogue_frame, wrap=tk.WORD, font=("Helvetica", 16),
                            bg="#34495E", fg="#ECF0F1", relief=tk.FLAT,
                            padx=20, pady=20)
        
        scrollbar = tk.Scrollbar(dialogue_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add dialogue lines
        dialogue_lines = event.get('dialogue', [])
        if dialogue_lines:
            for line in dialogue_lines:
                # Format dialogue with speaker formatting
                if ':' in line:
                    speaker, text = line.split(':', 1)
                    text_widget.insert(tk.END, f"{speaker.strip()}:", "speaker")
                    text_widget.insert(tk.END, f" {text.strip()}\n\n")
                else:
                    text_widget.insert(tk.END, f"{line}\n\n")

        # Configure speaker tag for better formatting
        text_widget.tag_configure("speaker", foreground="#3498DB", font=("Helvetica", 16, "bold"))

        # Make text read-only
        text_widget.config(state=tk.DISABLED)

        # Right side - GIF (if specified in JSON)
        if gif_path:
            try:
                # Load GIF frames
                gif_frames = self.load_gif_frames(gif_path)
                if gif_frames:
                    # Create frame for GIF on the right
                    gif_frame = tk.Frame(content_container, bg="#2C3E50")
                    gif_frame.pack(side=tk.RIGHT, fill=tk.Y)
                    
                    # Create label for GIF
                    gif_label = tk.Label(gif_frame, bg="#2C3E50")
                    gif_label.pack(anchor=tk.N, pady=(20, 0))
                    
                    # Start GIF animation
                    self.gif_running = True
                    self.animate_gif_in_dialogue(gif_label, gif_frames, delay=100)
            except Exception as e:
                print(f"Error setting up GIF '{gif_path}': {e}")

        # Button frame at bottom
        button_frame = tk.Frame(main_frame, bg="#2C3E50")
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Continue button
        def close_dialogue():
            if hasattr(self, 'gif_running'):
                self.gif_running = False  # Stop GIF animation
            dialogue_window.destroy()

        continue_button = tk.Button(button_frame, text="Continue",
                                command=close_dialogue,
                                font=("Helvetica", 16, "bold"),
                                bg="#3498DB", fg="white", padx=30, pady=10)
        continue_button.pack(side=tk.RIGHT)

        # Handle window close
        def on_window_close():
            if hasattr(self, 'gif_running'):
                self.gif_running = False
            dialogue_window.destroy()

        dialogue_window.protocol("WM_DELETE_WINDOW", on_window_close)

        # Center the window
        dialogue_window.update_idletasks()
        x = (dialogue_window.winfo_screenwidth() // 2) - (dialogue_window.winfo_reqwidth() // 2)
        y = (dialogue_window.winfo_screenheight() // 2) - (dialogue_window.winfo_reqheight() // 2)
        dialogue_window.geometry(f"+{x}+{y}")

    def load_gif_frames(self, gif_path):
        """Load all frames from an animated GIF"""
        if not PIL_AVAILABLE:
            print("❌ PIL/Pillow not available - cannot load GIFs")
            return []
        
        try:
            # Get absolute path for debugging
            abs_path = os.path.abspath(gif_path)
            print(f"🔍 Attempting to load GIF: {gif_path}")
            print(f"🔍 Absolute path: {abs_path}")
            print(f"🔍 File exists: {os.path.exists(gif_path)}")
            
            # List all GIF files in current directory for debugging
            current_dir = os.getcwd()
            gif_files = [f for f in os.listdir(current_dir) if f.lower().endswith('.gif')]
            print(f"🔍 Available GIF files in {current_dir}: {gif_files}")
            
            # Check if file exists
            if not os.path.exists(gif_path):
                print(f"❌ GIF file not found: {gif_path}")
                return []
            
            print(f"✅ Loading GIF: {gif_path}")
            gif = Image.open(gif_path)
            frames = []
            
            try:
                while True:
                    # Convert frame to PhotoImage and resize for dialogue
                    frame = gif.copy()
                    frame = frame.convert('RGBA')
                    frame = frame.resize((500, 500), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(frame)
                    frames.append(photo)
                    gif.seek(len(frames))  # Go to next frame
            except EOFError:
                pass  # End of frames
            
            print(f"✅ Successfully loaded {len(frames)} frames from {gif_path}")
            return frames
        except Exception as e:
            print(f"❌ Error loading GIF '{gif_path}': {e}")
            import traceback
            traceback.print_exc()
            return []

    def animate_gif_in_dialogue(self, label, frames, delay=100):
        """Animate GIF frames in a dialogue label"""
        if not frames or not hasattr(self, 'gif_running') or not self.gif_running:
            return
        
        frame_index = 0
        
        def update_frame():
            if not hasattr(self, 'gif_running') or not self.gif_running or not frames:
                return
            
            nonlocal frame_index
            try:
                label.config(image=frames[frame_index])
                frame_index = (frame_index + 1) % len(frames)
                label.after(delay, update_frame)
            except tk.TclError:
                # Window was closed
                if hasattr(self, 'gif_running'):
                    self.gif_running = False
        
        update_frame()

    def regular_exploration(self, location_name):
        """Handle regular exploration results when no special events occur"""
        # Simple exploration results for now
        exploration_results = [
            "There doesn't seem to be much here worth exploring.",
        ]
        import random
        return random.choice(exploration_results)

    def update_player_info(self):
        """Modified to show XP and level"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        if hasattr(self, 'info_frame'):
            for widget in self.info_frame.winfo_children():
                widget.destroy()
        
            info_container = tk.Frame(self.info_frame, bg="#ADD8E6")
            info_container.pack(pady=5)
            
            # Make player name clickable with level
            name_level_text = f"👤 {self.player.name} (Lv.{self.player.level})"
            name_label = tk.Label(info_container, text=name_level_text, 
                                font=("Helvetica", 12, "bold"), bg="#ADD8E6", 
                                fg="blue", cursor="hand2")
            name_label.bind("<Button-1>", lambda e: self.open_inventory_window())
            name_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Rest of the stats with XP
            xp_progress = self.player.get_xp_progress()
            stats_text = f"❤️ {self.player.health}/{self.player.max_health} | 💰 {self.player.gold}g | ⚡ {self.player.energy} | ⭐ {self.player.get_xp_display()}"
            stats_label = tk.Label(info_container, text=stats_text, 
                                font=("Helvetica", 12), bg="#ADD8E6")
            stats_label.pack(side=tk.LEFT)
            
            # Add fishing license status to stats
            if hasattr(self.player, 'has_fishing_license') and self.player.has_fishing_license:
                stats_text += " | 🎫 Licensed"
            
            # XP progress bar
            if xp_progress < 100:  # Only show progress bar if not at max XP
                xp_bar_frame = tk.Frame(info_container, bg="#ADD8E6")
                xp_bar_frame.pack(side=tk.LEFT, padx=(10, 0))
                
                # Create simple text-based progress bar
                bar_width = 20
                filled_width = int((xp_progress / 100) * bar_width)
                empty_width = bar_width - filled_width
                progress_bar = "█" * filled_width + "░" * empty_width
                
                xp_bar_label = tk.Label(xp_bar_frame, text=f"[{progress_bar}] {xp_progress:.0f}%", 
                                       font=("Courier", 10), bg="#ADD8E6", fg="purple")
                xp_bar_label.pack()

    def begin_adventure(self):
        """Start the main game after character creation"""
        # Switch to start_adventure.gif
        self.switch_to_start_adventure_gif()
        
        # FIXED: Restart the animation after switching GIFs
        self.root.after(100, self.animate_gif)

        name = self.name_entry.get().strip()

        if not name:
            messagebox.showwarning("Missing Name", "Please enter your character's name!")
            return

            # Create player with entered information
        self.player = Player()
        self.player.name = name


        # Give player starting gear
        starting_gear_names = ["Old Rod", "Rusty Knife", "Old Shirt"]
        for gear_name in starting_gear_names:
            for gear_data in self.gear_data['gear']:
                if gear_data['name'] == gear_name:
                    starting_gear = Gear(gear_data)
                    starting_gear.equipped = False  # Start unequipped
                    self.player.gear_inventory.append(starting_gear)
                    break

        
        # Give player starting bait - pulled from JSON
        bait_found = False
        for item_data in self.item_data['items']:
            if item_data.get('name') == 'Bait':
                starting_bait = Item(item_data)
                self.player.add_item(starting_bait)
                bait_found = True
                self.log_message(f"🎣 Starting with {starting_bait.name}")
                break
        
        if not bait_found:
            print("❌ Warning: Bait not found in items.json!")
            self.log_message("⚠️ No starting bait available - you'll need to find or buy some!")

        self.setup_frame.pack_forget()
        self.create_main_game_interface()

    def catch_fish(self, location):
            """Catch a fish at this location"""
            if not hasattr(self, 'player') or self.player is None:
                return

            # Find fish that can be caught at this location
            available_fish = []
            for fish_data in self.fish_data['fish']:
                if fish_data['type'] in location.fish_types:
                    available_fish.append(fish_data)
        
            if not available_fish:
                return "No fish found at this location!"

            # Get player luck for rarity bonus
            player_luck = self.player.get_total_stats()['luck'] if hasattr(self, 'player') and self.player else 0

            # Weighted random selection by rarity with luck bonus
            weights = []
            for fish in available_fish:
                rarity = fish.get('rarity', 1)
                # Luck slightly increases weight for rarer fish (but not too much)
                luck_bonus = player_luck * (rarity / 4000)  # Small bonus for rare fish
                weight = max(1, 1000 - rarity + luck_bonus)
                weights.append(weight)
        
            selected_fish_data = random.choices(available_fish, weights=weights)[0]
            caught_fish = Fish(selected_fish_data)
        
            # Add to player's inventory
            self.player.add_fish(caught_fish)

            # Give XP based on fish rarity (1-3 XP for most fish)
            fish_xp = max(1, min(5, int(caught_fish.rarity / 20)))  # 1-5 XP based on rarity
            level_up_message = self.player.add_xp(fish_xp)

            # Check for fish effects from JSON data
            effect_message = ""
            if hasattr(caught_fish, 'fish_effect') and caught_fish.fish_effect != "none":
                effect_message = f" ✨ {caught_fish.fish_effect}!"

            result = f"🐟 Caught a {caught_fish.name} ({caught_fish.actual_size} inches)! Food value: {caught_fish.food_value} energy (+{fish_xp} XP){effect_message}"

            # HANDLE LEVEL UP BEFORE RETURNING
            if level_up_message:
                self.log_message(result)
                self.log_message(f"🎉 {level_up_message}")
                # Show level up choice after a short delay
                self.root.after(1000, lambda: self.show_level_up_choice(level_up_message))
            
            return result

    def catch_item(self, location):
        """Find an item while fishing"""
        if not hasattr(self, 'player') or self.player is None:
            return "No player found!"
        
        # Filter items that can be found at this location
        available_items = []
        for item_data in self.item_data['items']:
            item_type = item_data.get('item_type', '')
            # Check if this item type is allowed at this location
            if item_type in location.item_types:
                available_items.append(item_data)
        
        if not available_items:
            return "📦 Found something, but it crumbled away..."
        
        # Get player luck for rarity bonus
        player_luck = self.player.get_total_stats()['luck'] if hasattr(self, 'player') and self.player else 0

        # Weighted random selection by rarity with luck bonus
        weights = []
        for item in available_items:
            base_weight = max(1, 1000 - item.get('rarity', 1))
            luck_bonus = player_luck * 2  # 2 weight per luck point
            weights.append(base_weight + luck_bonus)

        found_item_data = random.choices(available_items, weights=weights)[0]
        found_item = Item(found_item_data)
        self.player.add_item(found_item)
        return f"📦 Found a {found_item.name}! {found_item.description}"

    def catch_gear(self, location):
            """Find gear while fishing with rarity-based selection and quantity limits"""
            if not hasattr(self, 'player') or self.player is None:
                return
        
            # Initialize world gear quantities if not exists
            if not hasattr(self, 'world_gear_quantities'):
                self.world_gear_quantities = {}
                for gear_data in self.gear_data['gear']:
                    gear_name = gear_data.get('name', '')
                    if gear_name:  # Only add gear with valid names
                        initial_quantity = gear_data.get('quantity', 1)  # Default 1 if not specified
                        self.world_gear_quantities[gear_name] = initial_quantity
        
            # Get player luck for rarity bonus
            player_luck = self.player.get_total_stats()['luck'] if hasattr(self, 'player') and self.player else 0

            # Filter available gear (positive rarity, quantity > 0)
            catchable_gear = []
            weights = []

            for gear_data in self.gear_data['gear']:
                rarity = gear_data.get('rarity', 0)
                gear_name = gear_data.get('name', '')
        
                # Check if gear is available (non-starting gear and quantity > 0)
                if (rarity >= 0 and 
                    gear_name and 
                    self.world_gear_quantities.get(gear_name, 0) > 0):
            
                    catchable_gear.append(gear_data)
                    # Higher rarity = lower weight, but luck gives small bonus to rare gear
                    luck_bonus = player_luck * (rarity / 2000)  # Small bonus for rare gear
                    weight = max(1, 100 - rarity + luck_bonus)
                    weights.append(weight)

            if not catchable_gear:
                return "🎣 No gear available in the world!"

            # Use weighted random selection
            found_gear_data = random.choices(catchable_gear, weights=weights)[0]
            found_gear = Gear(found_gear_data)
            self.player.add_gear(found_gear)
        
            # Decrease world quantity
            gear_name = found_gear.name
            self.world_gear_quantities[gear_name] -= 1
            quantity_left = self.world_gear_quantities[gear_name]

            # Give XP based on gear rarity (2-8 XP)
            gear_xp = max(2, min(10, int(found_gear.rarity / 10)))  # 2-10 XP based on rarity
            level_up_message = self.player.add_xp(gear_xp)

            # Rarity and quantity messages
            rarity_text = ""
            if found_gear.rarity >= 80:
                rarity_text = ""
            elif found_gear.rarity >= 50:
                rarity_text = ""
            elif found_gear.rarity >= 20:
                rarity_text = ""

            # Placeholder for quantity text
            quantity_text = ""
            if quantity_left <= 0:
                quantity_text = ""
            elif quantity_left <= 3:
                quantity_text = f""

            result = f"⚔️ Found {found_gear.name}!{rarity_text} {found_gear.description}{quantity_text}"

            # Handle level up if it occurred
            if level_up_message:
                self.log_message(result)
                self.log_message(f"🎉 {level_up_message}")
                # Show level up choice after a short delay
                self.root.after(1000, lambda: self.show_level_up_choice(level_up_message))
            
            return result

    def create_main_game_interface(self):
            """Create the main game interface"""
            if not hasattr(self, 'player') or self.player is None:
                return
            self.game_frame = tk.Frame(self.root, bg="#87CEEB")
            self.game_frame.pack(fill=tk.BOTH, expand=True)

            # Player info panel
            self.info_frame = tk.Frame(self.game_frame, bg="#ADD8E6", relief=tk.RAISED, bd=2)
            self.info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

            self.update_player_info()

            # Action buttons frame
            self.action_frame = tk.Frame(self.game_frame, bg="#87CEEB")
            self.action_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

            # Location selection frame
            location_frame = tk.Frame(self.action_frame, bg="#87CEEB")
            location_frame.pack(side=tk.LEFT, padx=18)

            location_label = tk.Label(location_frame, text="Location:", 
                                font=("Helvetica", 12), bg="#87CEEB")
            location_label.pack(side=tk.LEFT, padx=(0, 5))

            # Get available locations
            available_locations = self.get_available_locations()
        
            # Create dropdown with available locations
            from tkinter import ttk
            self.location_var = tk.StringVar(value=available_locations[0] if available_locations else "Village Pond")
            self.location_dropdown = ttk.Combobox(location_frame, textvariable=self.location_var, 
                                            values=available_locations, state="readonly", width=15)
            self.location_dropdown.pack(side=tk.LEFT)

            # Fishing button
            self.fish_btn = tk.Button(self.action_frame, text="🎣 Go Fishing", 
                            font=("Helvetica", 14), bg="#2196F3", fg="white",
                            command=self.fishing_interface)
            self.fish_btn.pack(side=tk.LEFT, padx=3)

            # Sell items button
            self.sell_btn = tk.Button(self.action_frame, text="💰 Sell Items", 
                        font=("Helvetica", 14), bg="#4CAF50", fg="white",
                        command=self.open_sell_window)
            self.sell_btn.pack(side=tk.LEFT, padx=3)

            # Gear button
            self.gear_btn = tk.Button(self.action_frame, text="⚔️ Manage Gear", 
                        font=("Helvetica", 14), bg="#FF9800", fg="white",
                        command=self.open_gear_window)
            self.gear_btn.pack(side=tk.LEFT, padx=3)

            # Trade button
            self.trade_btn = tk.Button(self.action_frame, text="🎴 Trade", 
                    font=("Helvetica", 14), bg="#9C27B0", fg="white",
                    command=self.open_trade_window)
            self.trade_btn.pack(side=tk.LEFT, padx=3)

            # Items button (NEW)
            self.items_btn = tk.Button(self.action_frame, text="🧪 Use Items", 
                    font=("Helvetica", 14), bg="#607D8B", fg="white",
                    command=self.open_items_window)
            self.items_btn.pack(side=tk.LEFT, padx=3)

            # Eat Fish button (NEW)
            self.eat_fish_btn = tk.Button(self.action_frame, text="🍽️ Eat Fish", 
                    font=("Helvetica", 14), bg="#FF5722", fg="white",
                    command=self.open_eat_fish_window)
            self.eat_fish_btn.pack(side=tk.LEFT, padx=3)

            # Explore button (NEW)
            self.explore_btn = tk.Button(self.action_frame, text="🗺️ Explore", 
                    font=("Helvetica", 14), bg="#795548", fg="white",
                    command=self.explore_interface)
            self.explore_btn.pack(side=tk.LEFT, padx=3)

            # Game log
            self.log_frame = tk.Frame(self.game_frame, bg="#87CEEB")
            self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            log_label = tk.Label(self.log_frame, text="Adventure Log:", 
                            font=("Helvetica", 14, "bold"), bg="#87CEEB")
            log_label.pack(anchor=tk.W)

            self.game_log = tk.Text(self.log_frame, font=("Helvetica", 11), 
                            height=12, state=tk.DISABLED)
            self.game_log.pack(fill=tk.BOTH, expand=True)

            # Welcome message
            self.log_message(f"🎣 Welcome, {self.player.name}!")
            self.log_message("🌊 Your fishing adventure begins! Don't forget to equip your gear!")
            self.log_message("=" * 50)

    def get_available_locations(self):
        """Get list of locations available to the player"""
        available = []

        for loc_data in self.location_data['locations']:
            location = Location(loc_data)
            
            # Check if unlocked by default
            if location.unlocked_by_default:
                available.append(location.name)
            else:
                # Check if unlocked through exploration
                if (hasattr(self, 'player') and self.player and 
                    hasattr(self.player, 'unlocked_locations') and 
                    location.name in self.player.unlocked_locations):
                    available.append(location.name)
                # Also check for trade-unlocked locations
                elif location.is_unlocked(self.player.completed_trades if hasattr(self, 'player') and self.player else []):
                    available.append(location.name)

        return available if available else ["Village Pond"]

    def fishing_interface(self):
        """Handle fishing - costs 1 energy"""
        if hasattr(self, 'fish_btn'):
            self.fish_btn.config(state=tk.DISABLED)
        try:
            if not hasattr(self, 'player') or self.player is None:
                self.log_message("❌ No player found! Please start a new game.")
                return

            # Check if player is dead
            if self.player.health <= 0:
                self.log_message("💀 You cannot fish while defeated!")
                self.show_game_over_screen()
                return

            # Get selected location from dropdown
            selected_location = self.location_var.get()
            # Find the location data to check license requirement
            location_data = None
            for loc_data in self.location_data['locations']:
                if loc_data['name'] == selected_location:
                    location_data = Location(loc_data)
                    break
            
            # Check fishing license requirement BEFORE using energy
            if location_data and location_data.fishing_license_required:
                if not hasattr(self.player, 'has_fishing_license') or not self.player.has_fishing_license:
                    self.log_message(f"🚫 {selected_location} requires a Fishing License! Buy one from the Trade Deck.")
                    return

            # NEW: Check if player only has 1 energy left and confirm
            if self.player.energy == 1:
                confirm = messagebox.askyesno("Last Energy Warning", 
                                            "⚠️ You only have 1 energy left!\n\n"
                                            "Fishing will use your last energy and end your adventure.\n\n"
                                            "Are you sure you want to continue fishing?",
                                            icon='warning')
                if not confirm:
                    return  # Player chose not to fish

            if not self.player.use_energy(1):
                self.log_message("❌ Not enough energy to fish!")
                return

            result = self.go_fishing(selected_location)

            if selected_location == "Village Pond":
                self.switch_to_village_pond_cast_gif()
        
            # Check if enemy encountered and handle combat
            if result and "🦈 Enemy encountered!" in result:
                    # Find and start combat with enemy
                    location = None
                    for loc_data in self.location_data['locations']:
                        if loc_data['name'] == selected_location:
                            location = Location(loc_data)
                            break
                    
                    if location:
                        combat_result = self.encounter_enemy(location)
                        self.log_message(f"🌊 Fishing at {selected_location}: {combat_result}")
            else:
                    self.log_message(f"🌊 Fishing at {selected_location}: {result}")

                # Check for game over conditions after combat/fishing
            if self.player.health <= 0:
                    self.log_message("💀 GAME OVER! You have been defeated!")
                    self.root.after(1000, self.show_game_over_screen)
                    return
            elif self.player.is_game_over():
                    self.log_message("💀 GAME OVER! You ran out of energy!")
                    self.root.after(1000, self.show_game_over_screen)
                    return

            self.update_player_info()        

        finally:
            # Re-enable fishing button after a short delay
            if hasattr(self, 'fish_btn'):
                self.root.after(500, lambda: self.fish_btn.config(state=tk.NORMAL))

    def log_message(self, message):
            """Add a message to the game log"""
            if hasattr(self, 'game_log'):
                self.game_log.config(state=tk.NORMAL)
                self.game_log.insert(tk.END, f"{message}\n")
                self.game_log.config(state=tk.DISABLED)
                self.game_log.see(tk.END)

    def show_game_over_screen(self):
        """Show game over screen with restart option"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        self.fish_btn.config(state=tk.DISABLED)
        self.sell_btn.config(state=tk.DISABLED)
        self.trade_btn.config(state=tk.DISABLED)    

        self.game_over_window = tk.Toplevel(self.root)
        self.game_over_window.title("Game Over!")
        self.game_over_window.geometry("1600x1600")
        self.game_over_window.configure(bg="#2C3E50")
        self.game_over_window.resizable(True, True)

        self.game_over_window.transient(self.root)
        self.game_over_window.grab_set()

        title_label = tk.Label(self.game_over_window, text="💀 GAME OVER!", 
                        font=("Helvetica", 24, "bold"), bg="#2C3E50", fg="#E74C3C")
        title_label.pack(pady=20)

        # Determine cause of death
        if self.player.health <= 0:
            cause_label = tk.Label(self.game_over_window, text="You were defeated in combat!", 
                            font=("Helvetica", 16), bg="#2C3E50", fg="white")
        else:
            cause_label = tk.Label(self.game_over_window, text="You ran out of energy!", 
                            font=("Helvetica", 16), bg="#2C3E50", fg="white")
        cause_label.pack(pady=10)

        # Rest of the method stays the same...
        stats_frame = tk.Frame(self.game_over_window, bg="#34495E", relief=tk.RAISED, bd=2)
        stats_frame.pack(pady=20, padx=40, fill=tk.X)

        stats_title = tk.Label(stats_frame, text="Final Stats:", 
                        font=("Helvetica", 14, "bold"), bg="#34495E", fg="white")
        stats_title.pack(pady=5)

        fish_count = sum(1 for item in self.player.inventory if hasattr(item, 'actual_size'))
        item_count = sum(1 for item in self.player.inventory if hasattr(item, 'item_type'))
        gear_count = len(self.player.gear_inventory)

        stats_text = f"""👤 Fisher: {self.player.name}
    💰 Final Gold: {self.player.gold}g
    🐟 Fish Caught: {fish_count}
    📦 Items Found: {item_count}
    ⚔️ Gear Collected: {gear_count}"""

        stats_display = tk.Label(stats_frame, text=stats_text, 
                            font=("Helvetica", 12), bg="#34495E", fg="white",
                            justify=tk.LEFT)
        stats_display.pack(pady=10)

        button_frame = tk.Frame(self.game_over_window, bg="#2C3E50")
        button_frame.pack(pady=20)

        start_over_btn = tk.Button(button_frame, text="🔄 Start Over", 
                            font=("Helvetica", 14, "bold"), bg="#27AE60", fg="white",
                            command=self.restart_game, width=12)
        start_over_btn.pack(side=tk.LEFT, padx=10)

        quit_btn = tk.Button(button_frame, text="❌ Quit Game", 
                        font=("Helvetica", 14, "bold"), bg="#E74C3C", fg="white",
                        command=self.root.quit, width=12)
        quit_btn.pack(side=tk.LEFT, padx=10)

    def restart_game(self):
        """Restart the entire game by restarting the Python process"""
        import sys
        import os
        
        # Close game over window
        if hasattr(self, 'game_over_window') and self.game_over_window.winfo_exists():
            self.game_over_window.destroy()
        
        # Show a brief restart message
        restart_window = tk.Toplevel(self.root)
        restart_window.title("Restarting...")
        restart_window.geometry("300x100")
        restart_window.configure(bg="#2C3E50")
        restart_window.transient(self.root)
        restart_window.grab_set()
        
        restart_label = tk.Label(restart_window, text="🔄 Restarting game...", 
                                font=("Helvetica", 14), bg="#2C3E50", fg="white")
        restart_label.pack(expand=True)
        
        # Update the display
        restart_window.update()
        
        # Give a brief moment for the message to be visible
        self.root.after(500, self.execute_restart)

    def execute_restart(self):
        """Execute the actual restart"""
        import sys
        import os
        import subprocess
        
        try:
            # Get the current script path
            current_script = os.path.abspath(__file__)
            
            # Close the current Tkinter window
            self.root.quit()
            self.root.destroy()
            
            # Start a new instance of the same script
            subprocess.Popen([sys.executable, current_script])
            
            # Exit the current process
            sys.exit(0)
            
        except Exception as e:
            print(f"Error restarting: {e}")
            # Fallback to the old restart method if something goes wrong
            self.root.quit()

    def run(self):
            self.root.mainloop()

if __name__ == "__main__":
    game = FishingGame()
    game.run()