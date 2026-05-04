use once_cell::sync::Lazy;

pub struct ModeConfig {
    pub bm25_top_k_primary: usize,
    pub bm25_top_k_off: usize,
    pub ego_depth_default: usize,
    pub ego_depth_extended: usize,
}

impl Default for ModeConfig {
    fn default() -> Self {
        Self {
            bm25_top_k_primary: 1,
            bm25_top_k_off: 0,
            ego_depth_default: 1,
            ego_depth_extended: 2,
        }
    }
}

pub static MODE: Lazy<ModeConfig> = Lazy::new(ModeConfig::default);
