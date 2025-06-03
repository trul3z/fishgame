import tkinter as tk
from tkinter import messagebox 
import json
import random

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
        """Calculate gold value based on actual size vs average size"""
        size_multiplier = self.actual_size / self.avg_size
        # Size multiplier affects gold: bigger fish = more gold, smaller = less
        final_value = int(self.gold_value * size_multiplier)
        return max(1, final_value)  # Minimum 1 gold
    
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
            # Check if player has completed the "Venture Out" trade
            return "Venture Out" in player_trades_completed
        
        return False
    
    def __str__(self):
        return f"{self.name} - Fish: {', '.join(self.fish_types)} (Fish chance: {self.fish_spawn_chance})"

class Item:
    def __init__(self, item_data):
        self.name = item_data["name"]
        self.rarity = item_data["rarity"]
        self.value = item_data["value"]
        self.description = item_data["description"]
        self.item_type = item_data["item_type"]
        self.effect = item_data["effect"]
        self.quantity = item_data["quantity"]  # How many exist in the world

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
        self.description = trade_data["description"]
        self.trigger = trade_data["trigger"]  # Now a dictionary with structured data
    
    def execute_trigger(self, player, game):
        """Execute the trigger action based on structured trigger data"""
        action = self.trigger["action"]
        target = self.trigger["target"]
        
        if action == "add_gear":
            # Find gear in gear.json and add to player inventory
            for gear_data in game.gear_data['gear']:
                if gear_data['name'] == target:
                    gear = Gear(gear_data)
                    player.add_gear(gear)
                    return f"{target} added to inventory!"
            return f"Gear '{target}' not found!"
        
        elif action == "add_item":
            # Find item in items.json and add to player inventory
            for item_data in game.item_data['items']:
                if item_data['name'] == target:
                    item = Item(item_data)
                    player.add_item(item)
                    return f"{target} added to inventory!"
            return f"Item '{target}' not found!"
        
        elif action == "increase_stat":
            # Increase player stat by specified amount
            amount = self.trigger.get("amount", 1)
            if target == "luck":
                player.base_luck += amount
                return f"Luck increased by {amount}!"
            elif target == "skill":
                player.base_skill += amount
                return f"Skill increased by {amount}!"
            elif target == "health":
                player.max_health += amount
                player.health += amount
                return f"Max health increased by {amount}!"
        
        elif action == "unlock_locations":
            # Add completed trade to unlock locations
            player.completed_trades.append(self.name)
            return "New fishing locations unlocked!"
        
        elif action == "heal":
            # Heal player by amount or percentage
            amount = self.trigger.get("amount", 50)
            player.health = min(player.max_health, player.health + amount)
            return f"Healed for {amount} HP!"
        
        elif action == "add_gold":
            # Give player gold
            amount = self.trigger.get("amount", 100)
            player.gold += amount
            return f"Gained {amount} gold!"
        
        return f"Unknown action: {action}"
    
    def __str__(self):
        return f"{self.name} - {self.gold_value}g\n{self.description}\nEffect: {self.effect}"

class Player:
    def __init__(self):
        # Basic stats
        self.health = 10
        self.max_health = 10
        self.gold = 0  
        self.energy = 10 
        self.max_energy = 30
        self.level = 1
        self.xp = 0
        
        # Base stats (before equipment bonuses)
        self.base_luck = 3
        self.base_attack = 3
        self.base_defense = 3
        self.base_speed = 3

        self.name = ""
        self.backstory = ""
        self.age = 0

        # Inventory
        self.inventory = []  
        self.gear_inventory = [] 
        self.completed_trades = []  
        
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

    def sell_fish(self, fish):
        """Sell a fish for gold"""
        if fish in self.inventory:
            gold_earned = fish.gold_value()
            self.gold += gold_earned
            self.inventory.remove(fish)
            return f"💰 Sold {fish.name} for {gold_earned} gold!"
        return "Fish not found in inventory!"
    
    def sell_item(self, item):
        """Sell an item for gold"""
        if item in self.inventory:
            gold_earned = item.gold_value()
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
            if gear and gear.stat_bonus:
                total_luck += gear.stat_bonus.get("luck", 0)
                total_attack += gear.stat_bonus.get("attack", 0)
                total_defense += gear.stat_bonus.get("defense", 0)
                total_speed += gear.stat_bonus.get("speed", 0)

        # Add bonuses from fish in inventory
        fish_bonuses = self.get_fish_bonuses()
        total_luck += fish_bonuses["luck"]
        total_attack += fish_bonuses["attack"]
        total_defense += fish_bonuses["defense"]
        total_speed += fish_bonuses["speed"]

        return {
            "luck": total_luck,
            "attack": total_attack,
            "defense": total_defense,
            "speed": total_speed
        }
    
    def use_item(self, item):
        """Use a consumable item"""
        if item.item_type == "consumable":
            if "restore" in item.effect and "health" in item.effect:
                # Extract health amount (e.g., "restore 50 health")
                import re
                health_match = re.search(r'restore (\d+) health', item.effect)
                if health_match:
                    heal_amount = int(health_match.group(1))
                    self.health = min(self.max_health, self.health + heal_amount)
                    self.inventory.remove(item)
                    return f"Restored {heal_amount} health!"
            
            elif "increase" in item.effect and "skill" in item.effect:
                # Ancient Scroll effect
                self.base_skill += 3
                self.inventory.remove(item)
                return "Your fishing skill increased by 3!"
        
        return "Item cannot be used."

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
        self.root.title("Tyler's Fishing Game")
        self.root.geometry("1260x720")  
        self.root.resizable(True, True)
        self.root.configure(bg="#87CEEB")
        self.create_widgets()
        self.load_json_data()

    def create_widgets(self):
        self.title_label = tk.Label(self.root, text="Tyler's Fishing Game", font=("Helvetica", 24), bg="#87CEEB")
        self.title_label.pack(pady=20)

        self.start_button = tk.Button(self.root, text="Start Game", font=("Helvetica", 18), command=self.start_game)
        self.start_button.pack(pady=10)
    
        self.quit_button = tk.Button(self.root, text="Quit", font=("Helvetica", 18), command=self.root.quit)
        self.quit_button.pack(pady=10)

    def load_json_data(self):
        """Load all the JSON files"""
        try:
            with open("C:/Users/tman8/Desktop/fishgame/fish.json", "r") as f:
                self.fish_data = json.load(f)
            print("✅ Fish data loaded successfully")

            with open("C:/Users/tman8/Desktop/fishgame/items.json", "r") as f:
                self.item_data = json.load(f)
            print("✅ Item data loaded successfully")

            with open("C:/Users/tman8/Desktop/fishgame/gear.json", "r") as f:
                self.gear_data = json.load(f)
            print("✅ Gear data loaded successfully")
            
            with open("C:/Users/tman8/Desktop/fishgame/enemies.json", "r") as f:
                self.enemy_data = json.load(f)
            print("✅ Enemy data loaded successfully")
            
            with open("C:/Users/tman8/Desktop/fishgame/locations.json", "r") as f:
                self.location_data = json.load(f)
            print("✅ Location data loaded successfully")
            
            with open("C:/Users/tman8/Desktop/fishgame/trade.json", "r") as f:
                self.trade_data = json.load(f)
            print("✅ Trade data loaded successfully")
            
            print(f"Total loaded: {len(self.fish_data['fish'])} fish, {len(self.item_data['items'])} items, {len(self.gear_data['gear'])} gear, {len(self.enemy_data['enemies'])} enemies, {len(self.location_data['locations'])} locations, {len(self.trade_data['trade'])} trade options")
            
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            # Initialize empty data structures to prevent crashes
            self.fish_data = {'fish': []}
            self.item_data = {'items': []}
            self.gear_data = {'gear': []}
            self.enemy_data = {'enemies': []}
            self.location_data = {'locations': []}
            self.trade_data = {'trade': []}

    def go_fishing(self, location_name):
        """Go fishing at a location - can catch fish, items, gear, encounter enemies, or catch nothing"""
        # Find location
        location = None
        for loc_data in self.location_data['locations']:
            if loc_data['name'] == location_name:
                location = Location(loc_data)
                break
    
        if not location:
            return "Location not found!"
    
        # Stage 1: What happens when you cast your line? (cumulative probability)
        rand = random.random()
        cumulative = 0
    
        cumulative += location.fish_spawn_chance
        if rand < cumulative:
            return self.catch_fish(location)
    
        cumulative += location.item_spawn_chance
        if rand < cumulative:
            return self.catch_item(location)
    
        cumulative += location.gear_spawn_chance
        if rand < cumulative:
            return self.catch_gear(location)
    
        cumulative += location.enemy_spawn_chance
        if rand < cumulative:
            return "🦈 Enemy encountered!"
    
        # Catch nothing (remaining probability)
        return "🎣 Nothing caught... try again!"

    def encounter_enemy(self, location):
        """Encounter an enemy and start combat"""
        # Select random enemy from available enemies
        available_enemies = []
        for enemy_data in self.enemy_data['enemies']:
            if enemy_data['enemy_type'] in ['common']:  # Can expand this based on location
                available_enemies.append(enemy_data)
        
        if not available_enemies:
            return "🦈 Enemy encountered but none available!"
        
        enemy_data = random.choice(available_enemies)
        enemy = Enemy(enemy_data)
        
        # Start combat
        combat_result = self.start_combat(enemy)
        return combat_result

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
        
        # Initialize attack count if not set
        if not hasattr(self, 'current_attack_count'):
            self.current_attack_count = 0
        
        player_stats = self.player.get_total_stats()
        
        # Calculate damage
        base_damage = player_stats['attack']
        
        # Check for critical hit (luck increases crit chance)
        crit_chance = 5 + (player_stats['luck'] * 2)  # Base 5% + 2% per luck point
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
        """Enemy attacks the player"""
        if self.player_turn or not self.current_enemy.is_alive():
            return
        
        if not hasattr(self, 'player') or self.player is None:
            return

        # Initialize attack count if not set
        if not hasattr(self, 'current_attack_count'):
            self.current_attack_count = 0

        # Calculate enemy damage
        base_damage = self.current_enemy.attack
        player_stats = self.player.get_total_stats()
        
        # Player takes damage (reduced by defense)
        damage_taken = max(1, base_damage - player_stats['defense'])
        self.player.health -= damage_taken
        
 # Use the enemy's attack message if available, otherwise use default
        if hasattr(self.current_enemy, 'attack_message'):
            attack_msg = self.current_enemy.attack_message
        else:
            attack_msg = f"{self.current_enemy.name} attacks you!"
        
        self.add_combat_log(f"👹 {attack_msg}")
        self.add_combat_log(f"💔 You take {damage_taken} damage!")
        
        # Update player health display
        self.player_health_label.config(text=f"❤️ HP: {self.player.health}/{self.player.max_health}")
        
        # Check if player is defeated
        if self.player.health <= 0:
            self.combat_defeat()
            return
        
        # Increment attack count
        self.current_attack_count += 1
        
        # Check if enemy has more attacks this turn
        if self.current_attack_count < self.enemy_attacks_per_turn:
            # Continue attacking after a shorter delay
            if self.current_attack_count < self.enemy_attacks_per_turn - 1:
                self.add_combat_log(f"💫 {self.current_enemy.name} prepares another strike...")
            self.root.after(1000, self.enemy_turn)
            return
        
        # All attacks used, switch back to player turn
        self.current_attack_count = 0
        self.player_turn = True
        self.attack_btn.config(state=tk.NORMAL)
        self.flee_btn.config(state=tk.NORMAL)

    def attempt_flee(self):
        """Attempt to flee from combat"""
        if not self.player_turn:
            return
        
        if not hasattr(self, 'player') or self.player is None:
            return

        player_stats = self.player.get_total_stats()

        # Flee chance based on speed difference
        speed_diff = player_stats['speed'] - self.current_enemy.speed
        base_flee_chance = 50  # Base 50% chance
        flee_chance = base_flee_chance + (speed_diff * 10)  # +10% per speed point difference
        speed_bonus = speed_diff * 10  # +10% per speed point difference
        flee_chance = max(10, min(90, flee_chance))  # Clamp between 10% and 90%
        luck_bonus = player_stats['luck'] // 2  # +1% per luck point
        
        flee_chance = base_flee_chance + speed_bonus + luck_bonus
        flee_chance = max(10, min(95, flee_chance))  # Clamp between 10% and 95%
        
        flee_roll = random.randint(1, 100)
        self.add_combat_log(f"🎲 Flee attempt: {flee_roll} vs {flee_chance} (Speed: {speed_bonus:+}, Luck: {luck_bonus:+})")
        
        if flee_roll <= flee_chance:
            self.add_combat_log(f"🏃 You successfully fled from {self.current_enemy.name}!")
            self.root.after(1500, self.end_combat)
            self.log_message(f"🏃 Fled from {self.current_enemy.name}!")
        else:
            self.add_combat_log(f"❌ Failed to flee! {self.current_enemy.name} blocks your escape!")
            
            # Enemy gets a free attack (but only one, regardless of their normal attack count)
            self.player_turn = False
            self.attack_btn.config(state=tk.DISABLED)
            self.flee_btn.config(state=tk.DISABLED)
            self.current_attack_count = 0  # Reset for single punishment attack
            
            # Temporary override for single attack
            original_attacks = self.enemy_attacks_per_turn
            self.enemy_attacks_per_turn = 1
            
            def restore_attacks():
                self.enemy_attacks_per_turn = original_attacks
            
            self.root.after(1500, self.enemy_turn)
            self.root.after(3000, restore_attacks)

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
        self.player.xp += xp_reward

        self.add_combat_log(f"💰 You earned {gold_reward} gold!")
        if xp_reward > 0:
            self.add_combat_log(f"⭐ You gained {xp_reward} experience!")
        
        # Log victory in main game log
        self.log_message(f"⚔️ Defeated {self.current_enemy.name}! Earned {gold_reward} gold.")
        
        # End combat after delay
        self.root.after(1500, self.end_combat)

    def combat_defeat(self):
        """Player loses the combat"""
        if not hasattr(self, 'current_enemy') or not self.current_enemy.is_alive():
            return
        if not hasattr(self, 'player') or self.player is None:
            return
        self.add_combat_log(f"💀 Defeat! {self.current_enemy.name} has defeated you!")
        self.add_combat_log(f"💔 You lost some gold and items...")
        
        # Penalties for losing
        gold_lost = min(self.player.gold, self.player.gold // 4)  # Lose 25% of gold
        self.player.gold -= gold_lost
        
        # Set health to 1 (don't kill player completely)
        self.player.health = 1
        
        self.add_combat_log(f"💸 You lost {gold_lost} gold.")
        self.log_message(f"💀 Defeated by {self.current_enemy.name}! Lost {gold_lost} gold.")
        
        # End combat after delay
        self.root.after(3000, self.end_combat)

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

    def show_trade_deck(self):
        """Show 3 random trades for the player to choose from"""
        available_trades = random.sample(self.trade_data['trade'], 3)
        trades = [Trade(trade_data) for trade_data in available_trades]

        print("🎴 TRADE DECK - Choose wisely!")
        print("=" * 40)
        for i, trade in enumerate(trades, 1):
            print(f"{i}. {trade}")
            print("-" * 30)

        return trades

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
            "Whale", "Shark", "Ray", "Eel", "Crab", "Lobster", "Shrimp", "Kelp","Cthulu","Stinky","Big","Fishy","Bubbles","Splash","Gills","Finley","Hook","Reelina","Tidal","Nautical","Muhammad","Jesus","Lil"
        ]
        
        last_names = [
            "Angler", "Caster", "Fisher", "Netsman", "Hooker", "Baiter", "Reeler",
            "Sailor", "Mariner", "Seaman", "Captain", "Navigator", "Helmsman",
            "Tidewatcher", "Stormrider", "Wavebreaker", "Deepdiver", "Surfcaster",
            "Linecaster", "Rodmaster", "Baitlord", "Catchall", "Bigfish", "Longline",
            "Sinker", "Floater", "Dragnetter", "Spearman", "Harpoon", "Tackle",
            "Lighthouse", "Portside", "Starboard", "Windward", "Leeward", "Offshore","Cthulu","Jackson","Texas", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez", "Davis", "Rodriguez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Perez"
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
⚡ Energy: {self.player.energy}/{self.player.max_energy}
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
                                   yscrollcommand=scrollbar.set)
        self.gear_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.gear_listbox.yview)

    # Populate gear list
        self.refresh_gear_list()

    # Gear action buttons
        button_frame = tk.Frame(right_frame, bg="#FFE6E6")
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        equip_btn = tk.Button(button_frame, text="⚔️ Equip Selected", 
                         font=("Helvetica", 12), bg="#4CAF50", fg="white",
                         command=self.equip_selected_gear)
        equip_btn.pack(side=tk.LEFT, padx=5)

        unequip_btn = tk.Button(button_frame, text="📤 Unequip Selected", 
                           font=("Helvetica", 12), bg="#FF9800", fg="white",
                           command=self.unequip_selected_gear)
        unequip_btn.pack(side=tk.LEFT, padx=5)

    # Close button
        close_btn = tk.Button(self.gear_window, text="Close", 
                         font=("Helvetica", 12), bg="#757575", fg="white",
                         command=self.gear_window.destroy)
        close_btn.pack(pady=10)

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

    def update_player_info(self):
        """Update the player information display"""
        if not hasattr(self, 'player') or self.player is None:
            return
        
        if hasattr(self, 'info_frame'):
            for widget in self.info_frame.winfo_children():
                widget.destroy()
        
            info_container = tk.Frame(self.info_frame, bg="#ADD8E6")
        info_container.pack(pady=5)
        
        # Make player name clickable
        name_label = tk.Label(info_container, text=f"👤 {self.player.name}", 
                             font=("Helvetica", 12, "bold"), bg="#ADD8E6", 
                             fg="blue", cursor="hand2")
        name_label.bind("<Button-1>", lambda e: self.open_inventory_window())
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Rest of the stats
        stats_text = f"❤️ {self.player.health}/{self.player.max_health} | 💰 {self.player.gold}g | ⚡ {self.player.energy}/{self.player.max_energy}"
        stats_label = tk.Label(info_container, text=stats_text, 
                             font=("Helvetica", 12), bg="#ADD8E6")
        stats_label.pack(side=tk.LEFT)

    def begin_adventure(self):
        """Start the main game after character creation"""
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
    
        # Select random fish
        selected_fish_data = random.choice(available_fish)
        caught_fish = Fish(selected_fish_data)
    
        # Add to player's inventory
        self.player.add_fish(caught_fish)

        # Check for fish effects from JSON data
        effect_message = ""
        if hasattr(caught_fish, 'fish_effect') and caught_fish.fish_effect != "none":
            effect_message = f" ✨ {caught_fish.fish_effect}!"

        return f"🐟 Caught a {caught_fish.name} ({caught_fish.actual_size} inches)! Food value: {caught_fish.food_value} energy{effect_message}"

    def catch_item(self, location):
        """Find an item while fishing"""
        if not hasattr(self, 'player') or self.player is None:
            return
        found_item_data = random.choice(self.item_data['items'])
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
                # Higher rarity = lower weight (rarer)
                weight = max(1, 100 - rarity)
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

        return f"⚔️ Found {found_gear.name}!{rarity_text} {found_gear.description}{quantity_text}"

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

        # Fishing button
        self.fish_btn = tk.Button(self.action_frame, text="🎣 Go Fishing", 
                         font=("Helvetica", 14), bg="#2196F3", fg="white",
                         command=self.fishing_interface)
        self.fish_btn.pack(side=tk.LEFT, padx=5)

        # Location selection frame
        location_frame = tk.Frame(self.action_frame, bg="#87CEEB")
        location_frame.pack(side=tk.LEFT, padx=20)

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

        # Sell items button
        self.sell_btn = tk.Button(self.action_frame, text="💰 Sell Items", 
                     font=("Helvetica", 14), bg="#4CAF50", fg="white",
                     command=self.open_sell_window)
        self.sell_btn.pack(side=tk.LEFT, padx=5)

        # Gear button
        self.gear_btn = tk.Button(self.action_frame, text="⚔️ Manage Gear", 
                     font=("Helvetica", 14), bg="#FF9800", fg="white",
                     command=self.open_gear_window)
        self.gear_btn.pack(side=tk.LEFT, padx=5)

        # Game log
        self.log_frame = tk.Frame(self.game_frame, bg="#87CEEB")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        log_label = tk.Label(self.log_frame, text="Adventure Log:", 
                        font=("Helvetica", 14, "bold"), bg="#87CEEB")
        log_label.pack(anchor=tk.W)

        self.game_log = tk.Text(self.log_frame, font=("Helvetica", 11), 
                           height=15, state=tk.DISABLED)
        self.game_log.pack(fill=tk.BOTH, expand=True)

        # Welcome message
        self.log_message(f"🎣 Welcome, {self.player.name}!")
        self.log_message("🌊 Your fishing adventure begins! Don't forget to equip your gear!")
        self.log_message("=" * 50)

    def get_available_locations(self):
        """Get list of locations available to the player"""
        available = []
    
        # For now, just return all unlocked by default locations
        # Later we can add logic for completed_trades when that system is implemented
        for loc_data in self.location_data['locations']:
            location = Location(loc_data)
            if location.unlocked_by_default:
                available.append(location.name)
    
        return available if available else ["Village Pond"]

    def fishing_interface(self):
        """Handle fishing - costs 1 energy"""
        if not hasattr(self, 'player') or self.player is None:
            return

        # Check if player is dead
        if self.player.health <= 0:
            self.log_message("💀 You cannot fish while defeated!")
            self.show_game_over_screen()
            return

        if not self.player.use_energy(1):
            self.log_message("❌ Not enough energy to fish!")
            return

        # Get selected location from dropdown
        selected_location = self.location_var.get()
        result = self.go_fishing(selected_location)

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

        if self.player.is_game_over():
            self.log_message("💀 GAME OVER! You ran out of energy!")
            self.root.after(1000, self.show_game_over_screen)

        self.update_player_info()

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

        energy_label = tk.Label(self.game_over_window, text="You ran out of energy!", 
                           font=("Helvetica", 16), bg="#2C3E50", fg="white")
        energy_label.pack(pady=10)
    
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
        """Restart the entire game"""
        if hasattr(self, 'game_over_window'):
            self.game_over_window.destroy()
    
        for window_attr in ['sell_window', 'inventory_window', 'gear_window']:
            if hasattr(self, window_attr):
                window = getattr(self, window_attr)
                if window and window.winfo_exists():
                    window.destroy()
    
        if hasattr(self, 'game_frame'):
            self.game_frame.destroy()
    
        self.player = None
    
        self.create_widgets()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = FishingGame()
    game.run()