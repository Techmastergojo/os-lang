# FAT32 File System Partition Header Driver in OS-Lang
@packed
hwmap FAT32BootSector:
    bytes_per_sector: u16
    sectors_per_cluster: u8
    reserved_sector_count: u16
    table_count: u8
    root_entry_count: u16
    total_sectors_16: u16
    media_type: u8
    table_size_16: u16
    sectors_per_track: u16
    head_side_count: u16
    hidden_sector_count: u32
    total_sectors_32: u32
    table_size_32: u32
    extended_flags: u16
    fat_version: u16
    root_cluster: u32

@unsafe
fn fat32_read_root(boot: ptr[FAT32BootSector]) -> u32:
    let bytes_sec: u16 = boot.bytes_per_sector
    let root_cluster: u32 = boot.root_cluster
    return root_cluster
