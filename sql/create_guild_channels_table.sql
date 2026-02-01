-- Create guild_channels table for TTS channel configuration
-- This table stores which channels should have TTS enabled per guild

CREATE TABLE IF NOT EXISTS guild_channels (
    -- Primary key (auto-increment)
    id SERIAL PRIMARY KEY,

    -- Discord guild (server) ID
    guild_id BIGINT NOT NULL,

    -- Discord channel ID
    channel_id BIGINT NOT NULL,

    -- Creation timestamp
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one entry per guild-channel pair
    CONSTRAINT uq_guild_channel UNIQUE (guild_id, channel_id)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_guild_channels_guild_id ON guild_channels(guild_id);
CREATE INDEX IF NOT EXISTS idx_guild_channels_channel_id ON guild_channels(channel_id);

-- Add comments to columns
COMMENT ON TABLE guild_channels IS 'TTS-enabled channels per Discord guild';
COMMENT ON COLUMN guild_channels.id IS 'Primary key';
COMMENT ON COLUMN guild_channels.guild_id IS 'Discord guild (server) ID';
COMMENT ON COLUMN guild_channels.channel_id IS 'Discord channel ID';
COMMENT ON COLUMN guild_channels.created_at IS 'Creation timestamp';
