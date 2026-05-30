import os
import shutil

# --- FILE PATHS ---
LUA_TARGET = os.path.join("ChallengeData", "Scripts", "challenge", "ChallengeGame.lua")

START_TAG = "-- === HIDE AND SEEK CORE MOD START ==="

LUA_PAYLOAD = """
-- === HIDE AND SEEK CORE MOD START ===
-- This block was automatically injected by sm_injector.py

-- Client-side network receiver for rendering messages
function ChallengeGame.client_hsmsg( self, params )
	if params and params.msg then
		sm.gui.chatMessage( params.msg )
	end
end

-- Client-side network receiver for syncing roles and nametags
function ChallengeGame.client_hsSync( self, params )
	self.client_hsRoles = params.roles
	self.client_hsActive = params.active
end

-- Server-side broadcast to all players
function ChallengeGame.hs_broadcast( self, msg )
	if not self.network then return end
	local allPlayers = sm.player.getAllPlayers()
	if allPlayers then
		for _, p in ipairs( allPlayers ) do
			self.network:sendToClient( p, "client_hsmsg", { msg = msg } )
		end
	end
end

-- Server-side whisper to a single player
function ChallengeGame.hs_whisper( self, player, msg )
	if not self.network then return end
	if player and type(player) == "userdata" then
		self.network:sendToClient( player, "client_hsmsg", { msg = msg } )
	else
		local allPlayers = sm.player.getAllPlayers()
		if allPlayers and #allPlayers > 0 then
			self.network:sendToClient( allPlayers[1], "client_hsmsg", { msg = msg } )
		end
	end
end

-- Server-side synchronizer to push state to clients for nametag management
function ChallengeGame.hs_syncRoles( self )
	if self.network then
		self.network:sendToClients( "client_hsSync", { roles = self.hs_roles, active = self.hs_active } )
	end
end

-- Initialize state safely
function ChallengeGame.hs_init( self )
	if self.hs_initialized then return end
	self.hs_active = false
	self.hs_baseRoles = {} -- Permanent roles that persist between rounds
	self.hs_roles = {}     -- Active roles for the current round
	self.hs_timer = 0
	self.hs_seekStartTime = 0
	
	-- Timers (Stored in ticks: 40 ticks = 1 second)
	self.hs_hidingTime = 40 * 120         -- Default: 2 minutes
	self.hs_hintInterval = 40 * 60       -- Default: 60 seconds
	self.hs_verbalHintTime = 40 * 60 * 5 -- Default: 5 minutes
	
	self.hs_phase = "hiding"
	self.hs_initialized = true
end

-- Start Game logic
function ChallengeGame.hs_startGame( self, caller )
	self:hs_init()
	if self.hs_active then
		if caller then self:hs_whisper( caller, "#ff0000[Hide & Seek] A match is already in progress!" ) end
		return
	end

	local allPlayers = sm.player.getAllPlayers()
	if #allPlayers < 2 then
		if caller then self:hs_whisper( caller, "#ffff00[Warning] Starting with less than 2 players (Testing mode)." ) end
	end

	local seekerCount, hiderCount = 0, 0
	for _, p in ipairs( allPlayers ) do
		if p and p.id then
			local currentRole = self.hs_baseRoles[p.id]
			if currentRole == "seeker" then seekerCount = seekerCount + 1
			elseif currentRole == "hider" then hiderCount = hiderCount + 1
			end
		end
	end

	if seekerCount == 0 or hiderCount == 0 then
		local seekerIdx = math.random( 1, #allPlayers )
		for i, p in ipairs( allPlayers ) do
			if p and p.id then
				if i == seekerIdx then
					self.hs_baseRoles[p.id] = "seeker"
				else
					self.hs_baseRoles[p.id] = "hider"
				end
			end
		end
	end

	self.hs_roles = {}
	for id, role in pairs( self.hs_baseRoles ) do
		self.hs_roles[id] = role
	end

	self.hs_active = true
	self.hs_timer = 0
	self.hs_seekStartTime = 0
	self.hs_phase = "hiding"
	
	self:hs_syncRoles()

	local starterName = caller and caller.name or "System"
	self:hs_broadcast( "#00ff00[Hide & Seek] Match started by " .. starterName .. "!" )
	self:hs_broadcast( "#ffff00[Phase: HIDING] Hiders have " .. math.floor(self.hs_hidingTime / 40) .. " seconds to hide! Seekers, freeze!" )
end

-- Stop Game logic
function ChallengeGame.hs_stopGame( self, reason )
	self:hs_init()
	if not self.hs_active then return end

	self.hs_active = false
	self:hs_syncRoles()
	
	local stopReason = reason or "Match stopped."
	self:hs_broadcast( "#ff9900[Hide & Seek] Game Over: " .. stopReason )
end

-- Proximity tag checking
function ChallengeGame.hs_checkProximity( self )
	if not self.hs_active or self.hs_phase ~= "seeking" then return end

	local allPlayers = sm.player.getAllPlayers()
	local seekers = {}
	local hiders = {}

	for _, p in ipairs( allPlayers ) do
		if p and p.id and p.character and sm.exists( p.character ) then
			local role = self.hs_roles[p.id]
			if role == "seeker" then
				table.insert( seekers, p )
			elseif role == "hider" then
				table.insert( hiders, p )
			end
		end
	end

	for _, seeker in ipairs( seekers ) do
		for _, hider in ipairs( hiders ) do
			if hider.character and sm.exists( hider.character ) and seeker.character and sm.exists( seeker.character ) then
				local sPos = seeker.character.worldPosition
				local hPos = hider.character.worldPosition
				local distance = ( sPos - hPos ):length()

				if distance <= 0.7 then
					self.hs_roles[hider.id] = "seeker"
					self:hs_broadcast( "#ff3333[Hide & Seek] " .. hider.name .. " was caught by " .. seeker.name .. "!" )
					self:hs_syncRoles()

					local remainingHiders = 0
					for _, p in ipairs( allPlayers ) do
						if p and p.id and self.hs_roles[p.id] == "hider" then
							remainingHiders = remainingHiders + 1
						end
					end

					if remainingHiders == 0 then
						local seekTime = math.floor((self.hs_timer - self.hs_seekStartTime) / 40)
						self:hs_stopGame( "All hiders caught! Seekers win in " .. seekTime .. " seconds!" )
						return
					end
				end
			end
		end
	end
end

-- Hook into server_onCreate
local old_server_onCreate = ChallengeGame.server_onCreate
function ChallengeGame.server_onCreate( self, ... )
	if old_server_onCreate then old_server_onCreate( self, ... ) end
	self:hs_init()
end

-- Hook into server_onFixedUpdate
local old_server_onFixedUpdate = ChallengeGame.server_onFixedUpdate
function ChallengeGame.server_onFixedUpdate( self, ... )
	if old_server_onFixedUpdate then old_server_onFixedUpdate( self, ... ) end

	self:hs_init()

	if self.server_challengeStarted then
		if not self.hs_active and not self.hs_autoStarted then
			self:hs_startGame()
			self.hs_autoStarted = true
		end
	else
		self.hs_autoStarted = false
	end

	if self.hs_active then
		self.hs_timer = self.hs_timer + 1

		if self.hs_phase == "hiding" then
			if self.hs_timer >= self.hs_hidingTime then
				self.hs_phase = "seeking"
				self.hs_seekStartTime = self.hs_timer
				self:hs_broadcast( "#ff0000[Phase: SEEKING] Time is up! Seekers are released!" )
			elseif (self.hs_hidingTime - self.hs_timer) % 400 == 0 then
				local timeLeft = math.floor((self.hs_hidingTime - self.hs_timer) / 40)
				if timeLeft > 0 then
					self:hs_broadcast( "#ffff00[Hide & Seek] " .. timeLeft .. " seconds remaining to hide!" )
				end
			end
		end
		
		if self.hs_phase == "seeking" then
			local seekTimer = self.hs_timer - self.hs_seekStartTime
			
			if self.hs_hintInterval > 0 and seekTimer > 0 and seekTimer % self.hs_hintInterval == 0 then
				self:hs_broadcast( "#00ffff[Hide & Seek] HINT TIME! All hiders must give a hint!" )
			end
			
			if self.hs_verbalHintTime > 0 and seekTimer == self.hs_verbalHintTime then
				self:hs_broadcast( "#ff00ff[Hide & Seek] VERBAL HINT PHASE BEGINS! Hiders must now use voice chat!" )
			end
		end

		if self.hs_timer % 5 == 0 then
			self:hs_checkProximity()
		end
	end
end

-- Hook into level resets
local old_server_onChallengeReset = ChallengeGame.server_onChallengeReset
function ChallengeGame.server_onChallengeReset( self, ... )
	if old_server_onChallengeReset then old_server_onChallengeReset( self, ... ) end
	if self.hs_active then
		self:hs_stopGame( "Challenge level was reset." )
	end
end

-- ==========================================
-- CLIENT SIDE HOOKS
-- ==========================================

local old_client_onCreate = ChallengeGame.client_onCreate
function ChallengeGame.client_onCreate( self, ... )
	if old_client_onCreate then old_client_onCreate( self, ... ) end

	sm.game.bindChatCommand( "/hhelp", {}, "client_onChatCommand", "Hide & Seek Help" )
	sm.game.bindChatCommand( "/startgame", {}, "client_onChatCommand", "Force start the match" )
	sm.game.bindChatCommand( "/stopgame", {}, "client_onChatCommand", "End the match" )
	sm.game.bindChatCommand( "/role", { { "string", "role", true }, { "string", "name", true } }, "client_onChatCommand", "Set custom roles (hider/seeker)" )
	sm.game.bindChatCommand( "/found", { { "string", "name", true } }, "client_onChatCommand", "Manually eliminate a hider" )
	
	-- Restored Timer Commands
	sm.game.bindChatCommand( "/hidingtime", { { "number", "mins", true } }, "client_onChatCommand", "Set hiding countdown (minutes)" )
	sm.game.bindChatCommand( "/hintinterval", { { "number", "secs", true } }, "client_onChatCommand", "Set hint frequency (seconds)" )
	sm.game.bindChatCommand( "/verbalhint", { { "number", "mins", true } }, "client_onChatCommand", "Set verbal hint phase start (minutes)" )
end

-- Smart Nametag Hider
local old_client_onFixedUpdate = ChallengeGame.client_onFixedUpdate
function ChallengeGame.client_onFixedUpdate( self, timeStep )
	if old_client_onFixedUpdate then old_client_onFixedUpdate( self, timeStep ) end
	
	if self.client_hsTick == nil then self.client_hsTick = 0 end
	self.client_hsTick = self.client_hsTick + 1
	
	-- Update nametags every 10 ticks for performance
	if self.client_hsTick % 10 == 0 then
		local localPlayer = sm.localPlayer.getPlayer()
		if localPlayer then
			for _, p in ipairs(sm.player.getAllPlayers()) do
				if p ~= localPlayer and p.character then
					if self.client_hsActive then
						local myRole = self.client_hsRoles and self.client_hsRoles[localPlayer.id]
						local theirRole = self.client_hsRoles and self.client_hsRoles[p.id]
						
						-- Only hide the nametag if I am a seeker and they are a hider
						if myRole == "seeker" and theirRole == "hider" then
							p.character:setNameTag("")
						else
							p.character:setNameTag(p:getName())
						end
					else
						-- Game is over, restore all names
						p.character:setNameTag(p:getName())
					end
				end
			end
		end
	end
end

function ChallengeGame.client_onChatCommand( self, params )
	if self.network then
		self.network:sendToServer( "server_hsCommand", params )
	end
end

-- Server receives the command and runs the logic
function ChallengeGame.server_hsCommand( self, params, player )
	if not params or not params[1] then return end
	local command = string.lower( params[1] )

	if command == "/hhelp" then
		self:hs_whisper( player, "#00ff00--- Hide & Seek Commands ---" )
		self:hs_whisper( player, "#ffff00/startgame #ffffff- Force starts the match." )
		self:hs_whisper( player, "#ffff00/stopgame #ffffff- Ends the match." )
		self:hs_whisper( player, "#ffff00/role [hider/seeker] [name] #ffffff- Set custom roles." )
		self:hs_whisper( player, "#ffff00/found [name] #ffffff- Manually catch a hider." )
		self:hs_whisper( player, "#ffff00/hidingtime [mins] #ffffff- Set hiding time in minutes." )
		self:hs_whisper( player, "#ffff00/hintinterval [secs] #ffffff- Set hint frequency." )
		self:hs_whisper( player, "#ffff00/verbalhint [mins] #ffffff- Set verbal hint start time." )

	elseif command == "/startgame" then
		self:hs_startGame( player )

	elseif command == "/stopgame" then
		self:hs_stopGame( "Match stopped by " .. (player.name or "Host") )
		
	-- Restored Command Handlers
	elseif command == "/hidingtime" then
		local mins = tonumber(params[2])
		if mins and mins > 0 then
			self.hs_hidingTime = mins * 60 * 40
			self:hs_broadcast( "#00ff00[Hide & Seek] Hiding time set to " .. mins .. " minutes." )
		else
			self:hs_whisper( player, "#ff3333[Error] Usage: /hidingtime [mins]" )
		end
		
	elseif command == "/hintinterval" then
		local secs = tonumber(params[2])
		if secs and secs > 0 then
			self.hs_hintInterval = secs * 40
			self:hs_broadcast( "#00ff00[Hide & Seek] Hint interval set to " .. secs .. " seconds." )
		else
			self:hs_whisper( player, "#ff3333[Error] Usage: /hintinterval [secs]" )
		end
		
	elseif command == "/verbalhint" then
		local mins = tonumber(params[2])
		if mins and mins > 0 then
			self.hs_verbalHintTime = mins * 60 * 40
			self:hs_broadcast( "#00ff00[Hide & Seek] Verbal hint phase begins at " .. mins .. " minutes." )
		else
			self:hs_whisper( player, "#ff3333[Error] Usage: /verbalhint [mins]" )
		end

	elseif command == "/found" then
		if not params[2] then return end
		local nameQuery = string.lower( tostring(params[2]) )
		local targetPlayer = nil
		
		for _, p in ipairs( sm.player.getAllPlayers() ) do
			if p and p.name and string.find( string.lower( p.name ), nameQuery, 1, true ) then
				targetPlayer = p
				break
			end
		end

		if targetPlayer and targetPlayer.id then
			if self.hs_roles[targetPlayer.id] == "hider" then
				self.hs_roles[targetPlayer.id] = "seeker"
				self:hs_broadcast( "#ff3333[Hide & Seek] " .. targetPlayer.name .. " was manually eliminated by " .. (player.name or "Host") .. "!" )
				self:hs_syncRoles()

				local remainingHiders = 0
				for _, p in ipairs( sm.player.getAllPlayers() ) do
					if p and p.id and self.hs_roles[p.id] == "hider" then
						remainingHiders = remainingHiders + 1
					end
				end

				if remainingHiders == 0 then
					local seekTime = 0
					if self.hs_phase == "seeking" then seekTime = math.floor((self.hs_timer - self.hs_seekStartTime) / 40) end
					self:hs_stopGame( "All hiders caught! Seekers win in " .. seekTime .. " seconds!" )
				end
			end
		end

	elseif command == "/role" then
		local targetRole = params[2] and string.lower( params[2] ) or ""
		if targetRole ~= "hider" and targetRole ~= "seeker" then return end

		local targetPlayer = player
		if params[3] then
			local nameQuery = string.lower( tostring(params[3]) )
			for _, p in ipairs( sm.player.getAllPlayers() ) do
				if p and p.name and string.find( string.lower( p.name ), nameQuery, 1, true ) then
					targetPlayer = p
					break
				end
			end
		end

		if targetPlayer and targetPlayer.id then
			self.hs_baseRoles = self.hs_baseRoles or {}
			self.hs_baseRoles[targetPlayer.id] = targetRole
			self.hs_roles[targetPlayer.id] = targetRole
			self:hs_broadcast( "#00ff00[Hide & Seek] " .. targetPlayer.name .. " is now a " .. targetRole .. "!" )
			self:hs_syncRoles()
		end
	end
end
-- === HIDE AND SEEK CORE MOD END ===
"""

def get_game_paths():
    print("--- Scrap Mechanic Core Mod Manager ---")
    game_path = input("Enter your Scrap Mechanic game installation path:\n> ").strip().strip('"').strip("'")
    
    if not os.path.exists(os.path.join(game_path, "ChallengeData")) and os.path.exists(os.path.join(game_path, "..", "ChallengeData")):
        game_path = os.path.abspath(os.path.join(game_path, ".."))

    lua_file_path = os.path.join(game_path, LUA_TARGET)
    lua_backup_path = lua_file_path + ".bak"
    
    return lua_file_path, lua_backup_path

def inject_mod(lua_file, lua_backup):
    if os.path.exists(lua_file):
        with open(lua_file, "r", encoding="utf-8") as f:
            content = f.read()
        if START_TAG in content:
            print("\n[*] Old Lua version found. Cleaning it up to update...")
            uninject_mod(lua_file, lua_backup, silent=True)

    try:
        if not os.path.exists(lua_backup):
            shutil.copy2(lua_file, lua_backup)
            print(f"\n[*] Created pristine Lua backup at: {os.path.basename(lua_backup)}")
        
        with open(lua_file, "a", encoding="utf-8") as f:
            f.write("\n" + LUA_PAYLOAD.strip())
        print("[+] SUCCESS: Lua Hide & Seek mechanics injected successfully.")
    except Exception as e:
        print(f"\n[X] Error during Lua injection: {e}")

def uninject_mod(lua_file, lua_backup, silent=False):
    if os.path.exists(lua_backup):
        try:
            shutil.copy2(lua_backup, lua_file)
            if not silent: print("\n[+] SUCCESS: Lua mechanics successfully restored to vanilla.")
        except Exception as e:
            if not silent: print(f"\n[X] Error restoring Lua backup: {e}")
    elif not silent:
        print("\n[X] No Lua backup found to restore.")

def main():
    paths = get_game_paths()
    if not paths[0]: return

    while True:
        print("\n==================================")
        print("[1] INJECT Hide & Seek Mod")
        print("[2] UNINJECT & RESTORE to Vanilla")
        print("[3] EXIT")
        print("==================================")
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            inject_mod(paths[0], paths[1])
        elif choice == "2":
            uninject_mod(paths[0], paths[1])
        elif choice == "3":
            print("Exiting manager.")
            break
        else:
            print("Invalid input. Select 1, 2, or 3.")

if __name__ == "__main__":
    main()