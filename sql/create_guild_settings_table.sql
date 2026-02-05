-- Create guild_settings table for guild-specific settings
-- This table stores default voice channel for each guild

CREATE TABLE IF NOT EXISTS guild_settings (
    -- Primary key (auto-increment)
    id SERIAL PRIMARY KEY,

    -- Discord guild (server) ID (unique)
    guild_id BIGINT NOT NULL UNIQUE,

    -- Default voice channel ID for TTS
    default_voice_channel_id BIGINT,

    -- Creation timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Last update timestamp
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_guild_settings_guild_id ON guild_settings(guild_id);

-- Add comments to columns
COMMENT ON TABLE guild_settings IS 'Guild-specific settings including default voice channel';
COMMENT ON COLUMN guild_settings.id IS 'Primary key';
COMMENT ON COLUMN guild_settings.guild_id IS 'Discord guild (server) ID';
COMMENT ON COLUMN guild_settings.default_voice_channel_id IS 'Default voice channel ID for auto-join TTS';
COMMENT ON COLUMN guild_settings.created_at IS 'Creation timestamp';
COMMENT ON COLUMN guild_settings.updated_at IS 'Last update timestamp';

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_guild_settings_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function on UPDATE
DROP TRIGGER IF EXISTS update_guild_settings_updated_at ON guild_settings;
CREATE TRIGGER update_guild_settings_updated_at
    BEFORE UPDATE ON guild_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_guild_settings_updated_at_column();
