package com.luckymod.client;

import org.lwjgl.opengl.GL11;

import com.luckymod.LuckyMod;

import net.minecraft.client.renderer.entity.RenderLiving;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityLivingBase;
import net.minecraft.util.ResourceLocation;

public class RenderLucky extends RenderLiving {

    private static final ResourceLocation TEXTURE =
            new ResourceLocation(LuckyMod.MODID, "textures/entity/lucky.png");

    public RenderLucky() {
        super(new ModelLucky(), 0.3F);
    }

    @Override
    protected ResourceLocation getEntityTexture(Entity entity) {
        return TEXTURE;
    }

    /**
     * The ears, face fur and whiskers are flat planes. 1.7.10 renders mobs with face culling off,
     * which would make both sides of a plane flicker over each other, so cull while drawing Lucky.
     */
    @Override
    protected void renderModel(EntityLivingBase entity, float limbSwing, float limbSwingAmount, float age,
            float headYaw, float headPitch, float scale) {
        GL11.glEnable(GL11.GL_CULL_FACE);
        super.renderModel(entity, limbSwing, limbSwingAmount, age, headYaw, headPitch, scale);
        GL11.glDisable(GL11.GL_CULL_FACE);
    }
}
