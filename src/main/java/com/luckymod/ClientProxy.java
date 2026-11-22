package com.luckymod;

import com.luckymod.client.RenderLucky;
import com.luckymod.entity.EntityLucky;

import cpw.mods.fml.client.registry.RenderingRegistry;

public class ClientProxy extends CommonProxy {

    @Override
    public void registerRenderers() {
        RenderingRegistry.registerEntityRenderingHandler(EntityLucky.class, new RenderLucky());
    }
}
