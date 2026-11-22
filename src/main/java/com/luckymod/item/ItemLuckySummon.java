package com.luckymod.item;

import com.luckymod.LuckyMod;
import com.luckymod.entity.EntityLucky;

import net.minecraft.creativetab.CreativeTabs;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Facing;
import net.minecraft.util.MathHelper;
import net.minecraft.world.World;

/** Right-click a block to call Lucky. It arrives tamed by whoever used the item. */
public class ItemLuckySummon extends Item {

    public ItemLuckySummon() {
        setUnlocalizedName(LuckyMod.MODID + ".lucky_summon");
        setTextureName(LuckyMod.MODID + ":lucky_summon");
        setCreativeTab(CreativeTabs.tabMisc);
        setMaxStackSize(16);
    }

    @Override
    public boolean onItemUse(ItemStack stack, EntityPlayer player, World world, int x, int y, int z, int side,
            float hitX, float hitY, float hitZ) {
        if (world.isRemote) return true;

        x += Facing.offsetsXForSide[side];
        y += Facing.offsetsYForSide[side];
        z += Facing.offsetsZForSide[side];

        EntityLucky lucky = new EntityLucky(world);
        float yaw = MathHelper.wrapAngleTo180_float(world.rand.nextFloat() * 360.0F);
        lucky.setLocationAndAngles(x + 0.5D, y, z + 0.5D, yaw, 0.0F);
        lucky.rotationYawHead = yaw;
        lucky.renderYawOffset = yaw;
        world.spawnEntityInWorld(lucky);
        lucky.tameBy(player);
        if (stack.hasDisplayName()) lucky.setCustomNameTag(stack.getDisplayName());
        else lucky.setCustomNameTag("Lucky");

        if (!player.capabilities.isCreativeMode) --stack.stackSize;
        return true;
    }
}
