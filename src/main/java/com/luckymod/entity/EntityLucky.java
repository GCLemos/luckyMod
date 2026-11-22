package com.luckymod.entity;

import com.luckymod.LuckyMod;

import net.minecraft.entity.EntityAgeable;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.entity.SharedMonsterAttributes;
import net.minecraft.entity.passive.EntityAnimal;
import net.minecraft.entity.passive.EntityWolf;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.item.ItemFood;
import net.minecraft.item.ItemShears;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.util.ChunkCoordinates;
import net.minecraft.util.DamageSource;
import net.minecraft.world.World;

/**
 * Lucky: a small shaggy terrier. Behaves like a tamed wolf (follows, defends its owner) and, when the
 * config says so, cannot die.
 * Right-click: pet. Sneak + right-click: sit / stand. Right-click with shears: trim the coat, which
 * grows back after a while.
 */
public class EntityLucky extends EntityWolf {

    private static final int SHEARED_WATCHER = 21;
    /** Entity-state byte sent to clients when Lucky is petted (vanilla uses 2..8). */
    private static final byte PET_EVENT = 40;
    private static final int PET_TICKS = 40;
    private static final String BARK = LuckyMod.MODID + ":lucky.bark";
    private static final String BARK_ANGRY = LuckyMod.MODID + ":lucky.bark_angry";

    private int furRegrowTicks;
    private int petTicks; // client only

    public EntityLucky(World world) {
        super(world);
        setSize(0.5F, 0.9F);
        if (LuckyMod.immortal) {
            isImmuneToFire = true;
        }
    }

    @Override
    protected void entityInit() {
        super.entityInit();
        dataWatcher.addObject(SHEARED_WATCHER, Byte.valueOf((byte) 0));
    }

    public boolean isSheared() {
        return dataWatcher.getWatchableObjectByte(SHEARED_WATCHER) != 0;
    }

    public void setSheared(boolean sheared) {
        dataWatcher.updateObject(SHEARED_WATCHER, Byte.valueOf((byte) (sheared ? 1 : 0)));
    }

    @Override
    public boolean interact(EntityPlayer player) {
        ItemStack held = player.inventory.getCurrentItem();

        if (held != null && held.getItem() instanceof ItemShears) {
            if (isSheared()) return true; // nothing left to trim yet
            if (!worldObj.isRemote) {
                setSheared(true);
                furRegrowTicks = LuckyMod.furRegrowTicks;
                held.damageItem(1, player);
                playSound("mob.sheep.shear", 1.0F, 1.0F);
            }
            return true;
        }

        if (player.isSneaking()) {
            if (!isTamed() || !func_152114_e(player)) return false; // only the owner gives orders
            if (!worldObj.isRemote) {
                aiSit.setSitting(!isSitting());
                isJumping = false;
                setPathToEntity(null);
                setTarget(null);
                setAttackTarget(null);
            }
            return true;
        }

        // hungry for real: let the wolf code eat the meat and heal
        if (held != null && held.getItem() instanceof ItemFood
                && ((ItemFood) held.getItem()).isWolfsFavoriteMeat() && getHealth() < getMaxHealth()) {
            return super.interact(player);
        }

        if (!worldObj.isRemote) {
            worldObj.setEntityState(this, PET_EVENT);
            playSound("mob.wolf.panting", getSoundVolume(), getSoundPitch());
        }
        return true;
    }

    @Override
    public void handleHealthUpdate(byte id) {
        if (id == PET_EVENT) {
            petTicks = PET_TICKS;
            playTameEffect(true); // hearts
        } else {
            super.handleHealthUpdate(id);
        }
    }

    /** 0..1, how far through a petting Lucky is (drives the happy animation). */
    public float getPetAmount(float partialTicks) {
        if (petTicks <= 0) return 0.0F;
        return Math.min(1.0F, (petTicks - partialTicks) / PET_TICKS);
    }

    @Override
    public void onUpdate() {
        super.onUpdate();
        if (worldObj.isRemote) {
            if (petTicks > 0) --petTicks;
        } else if (isSheared() && --furRegrowTicks <= 0) {
            setSheared(false); // the coat is back
        }
    }

    @Override
    public void writeEntityToNBT(NBTTagCompound tag) {
        super.writeEntityToNBT(tag);
        tag.setBoolean("Sheared", isSheared());
        tag.setInteger("FurRegrowTicks", furRegrowTicks);
    }

    @Override
    public void readEntityFromNBT(NBTTagCompound tag) {
        super.readEntityFromNBT(tag);
        setSheared(tag.getBoolean("Sheared"));
        furRegrowTicks = tag.getInteger("FurRegrowTicks");
    }

    @Override
    protected void applyEntityAttributes() {
        super.applyEntityAttributes();
        getEntityAttribute(SharedMonsterAttributes.maxHealth).setBaseValue(20.0D);
        getEntityAttribute(SharedMonsterAttributes.movementSpeed).setBaseValue(0.32D);
    }

    @Override
    public boolean attackEntityFrom(DamageSource source, float amount) {
        if (LuckyMod.immortal && !isRemovalBy(source)) {
            return false; // swords, mobs, lava, fall, drowning, potions, explosions... nothing hurts
        }
        return super.attackEntityFrom(source, amount);
    }

    /** A creative-mode player who sneaks and hits Lucky can still remove it. */
    private boolean isRemovalBy(DamageSource source) {
        if (!(source.getEntity() instanceof EntityPlayer)) return false;
        EntityPlayer player = (EntityPlayer) source.getEntity();
        return player.capabilities.isCreativeMode && player.isSneaking();
    }

    @Override
    public boolean attackEntityAsMob(net.minecraft.entity.Entity target) {
        // a small dog bites softer than a wolf, and tells everyone about it
        if (rand.nextInt(2) == 0) playSound(BARK_ANGRY, getSoundVolume(), pitchFor(BARK_ANGRY));
        return target.attackEntityFrom(DamageSource.causeMobDamage(this), isTamed() ? 3.0F : 2.0F);
    }

    @Override
    public void onLivingUpdate() {
        super.onLivingUpdate();
        if (worldObj.isRemote || !LuckyMod.immortal) return;

        if (getHealth() < getMaxHealth()) setHealth(getMaxHealth());
        if (isBurning()) extinguish();
        if (getAir() < 300) setAir(300);

        if (posY < -16.0D) rescueFromVoid();
    }

    /** Fell out of the world: come back to the owner, or to the world spawn. */
    private void rescueFromVoid() {
        motionX = motionY = motionZ = 0.0D;
        fallDistance = 0.0F;
        EntityLivingBase owner = getOwner();
        if (owner != null && owner.worldObj == worldObj) {
            setPositionAndUpdate(owner.posX, owner.posY, owner.posZ);
            return;
        }
        ChunkCoordinates spawn = worldObj.getSpawnPoint();
        int y = worldObj.getTopSolidOrLiquidBlock(spawn.posX, spawn.posZ);
        setPositionAndUpdate(spawn.posX + 0.5D, y + 1.0D, spawn.posZ + 0.5D);
    }

    @Override
    protected boolean canDespawn() {
        return false;
    }

    @Override
    protected float getSoundPitch() {
        return super.getSoundPitch() * 1.35F; // tiny dog: the wolf's panting/whining, pitched up
    }

    /** Real Yorkshire barks: a normal one, and an angry one when Lucky is fighting. */
    @Override
    protected String getLivingSound() {
        if (isAngry() || getAttackTarget() != null) return BARK_ANGRY;
        if (rand.nextInt(3) == 0) {
            return isTamed() && getHealth() < 10.0F ? "mob.wolf.whine" : "mob.wolf.panting";
        }
        return BARK;
    }

    @Override
    public void playLivingSound() {
        String sound = getLivingSound();
        if (sound != null) playSound(sound, getSoundVolume(), pitchFor(sound));
    }

    private float pitchFor(String sound) {
        // the recordings already are a small dog: only vary them slightly
        return sound.startsWith(LuckyMod.MODID) ? 0.95F + rand.nextFloat() * 0.1F : getSoundPitch();
    }

    // Lucky is one of a kind: no puppies, and it does not mate with regular wolves.
    @Override
    public boolean canMateWith(EntityAnimal other) {
        return false;
    }

    @Override
    public EntityWolf createChild(EntityAgeable other) {
        return null;
    }

    /** Called by the summon item: Lucky arrives already tamed by the player who used it. */
    public void tameBy(EntityPlayer player) {
        setTamed(true);
        setPathToEntity(null);
        setAttackTarget(null);
        func_152115_b(player.getUniqueID().toString()); // setOwnerUUID
        setHealth(getMaxHealth());
        worldObj.setEntityState(this, (byte) 7); // heart particles
    }
}
