package com.luckymod;

import com.luckymod.entity.EntityLucky;
import com.luckymod.item.ItemLuckySummon;

import cpw.mods.fml.common.Mod;
import cpw.mods.fml.common.SidedProxy;
import cpw.mods.fml.common.event.FMLInitializationEvent;
import cpw.mods.fml.common.event.FMLPreInitializationEvent;
import cpw.mods.fml.common.registry.EntityRegistry;
import cpw.mods.fml.common.registry.GameRegistry;
import net.minecraft.init.Blocks;
import net.minecraft.init.Items;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraftforge.common.config.Configuration;

@Mod(modid = LuckyMod.MODID, name = "Lucky", version = LuckyMod.VERSION)
public class LuckyMod {

    public static final String MODID = "luckymod";
    public static final String VERSION = "1.8.0";

    @Mod.Instance(MODID)
    public static LuckyMod instance;

    @SidedProxy(clientSide = "com.luckymod.ClientProxy", serverSide = "com.luckymod.CommonProxy")
    public static CommonProxy proxy;

    /** Config: config/luckymod.cfg -> general.immortal */
    public static boolean immortal = true;
    /** Config: general.furRegrowMinutes, converted to ticks. */
    public static int furRegrowTicks = 20 * 60 * 20;

    public static Item luckySummon;

    @Mod.EventHandler
    public void preInit(FMLPreInitializationEvent event) {
        Configuration config = new Configuration(event.getSuggestedConfigurationFile());
        config.load();
        immortal = config.getBoolean("immortal", Configuration.CATEGORY_GENERAL, true,
                "If true, Lucky never takes damage (only a sneaking creative-mode player can remove it).");
        int minutes = config.getInt("furRegrowMinutes", Configuration.CATEGORY_GENERAL, 20, 1, 1440,
                "Minutes (of game time) until Lucky's coat grows back after being trimmed with shears.");
        furRegrowTicks = minutes * 60 * 20;
        if (config.hasChanged()) config.save();

        EntityRegistry.registerModEntity(EntityLucky.class, "Lucky", 0, this, 80, 3, true);

        luckySummon = new ItemLuckySummon();
        GameRegistry.registerItem(luckySummon, "lucky_summon");

        proxy.registerRenderers();
    }

    @Mod.EventHandler
    public void init(FMLInitializationEvent event) {
        // Lucky's controller-shaped bed: black wool in a U, a melon slice inside, a ghast tear on top
        GameRegistry.addRecipe(new ItemStack(luckySummon), "WGW", "WMW", "WWW",
                'W', new ItemStack(Blocks.wool, 1, 15), 'G', Items.ghast_tear, 'M', Items.melon);
    }
}
