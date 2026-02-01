-- Create users table for TTS voice settings
-- This table stores per-user voice settings for each Discord guild (server)

CREATE TABLE IF NOT EXISTS users (
    -- Primary key (auto-increment)
    id SERIAL PRIMARY KEY,

    -- Discord user ID
    discord_id BIGINT NOT NULL,

    -- Discord guild (server) ID
    guild_id BIGINT NOT NULL,

    -- Discord username (for information)
    username VARCHAR(255) NOT NULL,

    -- Speech rate setting (percentage: 20-200, default: 100)
    -- 100 = normal speed, 150 = 1.5x speed, 50 = 0.5x speed
    rate INTEGER NOT NULL DEFAULT 100 CHECK (rate >= 20 AND rate <= 200),

    -- Speech pitch setting (percentage offset: -50 to +50, default: 0)
    -- 0 = normal pitch, +20 = higher pitch, -20 = lower pitch
    pitch INTEGER NOT NULL DEFAULT 0 CHECK (pitch >= -50 AND pitch <= 50),

    -- Creation timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Last update timestamp
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one setting per user per guild
    CONSTRAINT uq_user_guild UNIQUE (discord_id, guild_id)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id);
CREATE INDEX IF NOT EXISTS idx_users_guild_id ON users(guild_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_discord_guild ON users(discord_id, guild_id);

-- Add comments to columns
COMMENT ON TABLE users IS 'TTS voice settings per Discord user per guild';
COMMENT ON COLUMN users.id IS 'Primary key';
COMMENT ON COLUMN users.discord_id IS 'Discord user ID';
COMMENT ON COLUMN users.guild_id IS 'Discord guild (server) ID';
COMMENT ON COLUMN users.username IS 'Discord username';
COMMENT ON COLUMN users.rate IS 'Speech rate percentage (20-200, default: 100)';
COMMENT ON COLUMN users.pitch IS 'Speech pitch offset (-50 to +50, default: 0)';
COMMENT ON COLUMN users.created_at IS 'Creation timestamp';
COMMENT ON COLUMN users.updated_at IS 'Last update timestamp';

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function on UPDATE
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
