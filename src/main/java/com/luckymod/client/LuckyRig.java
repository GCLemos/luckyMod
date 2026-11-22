package com.luckymod.client;

import java.util.HashMap;
import java.util.Map;

import org.lwjgl.opengl.GL11;

import net.minecraft.client.model.ModelBase;
import net.minecraft.client.model.ModelBox;
import net.minecraft.client.model.ModelRenderer;

/**
 * One of Lucky's looks: world-aligned groups (body, head, ears, tail, four legs) holding the boxes
 * converted from the Better Dogs pack. LuckyRigs fills it; ModelLucky animates the groups.
 */
final class LuckyRig {

    private final ModelBase model;
    private final int texW, texH;
    private final Map<String, ModelRenderer> groups = new HashMap<String, ModelRenderer>();
    private final Map<String, float[]> rest = new HashMap<String, float[]>();

    /** The shaved look wears the cairn's head on a smaller chihuahua body, so it is drawn smaller. */
    float headScale = 1.0F;
    /** Whole-rig size, around the feet: the furry coat is shrunk to the shaved dog's height. */
    float scale = 1.0F;
    /**
     * Side-to-side wag axis (Y and Z weights): perpendicular to the tail, so a tail that points up
     * swings left-right instead of spinning around itself.
     */
    float tailWagY = 1.0F, tailWagZ = 0.0F;

    ModelRenderer body, head, earLeft, earRight, tail, legFrontLeft, legFrontRight, legBackLeft, legBackRight;

    LuckyRig(ModelBase model, int texW, int texH) {
        this.model = model;
        this.texW = texW;
        this.texH = texH;
    }

    void group(String name, String parent, float x, float y, float z) {
        ModelRenderer r = new ModelRenderer(model);
        r.setTextureSize(texW, texH);
        r.setRotationPoint(x, y, z);
        groups.put(name, r);
        rest.put(name, new float[] { x, y, z });
        if (parent != null) groups.get(parent).addChild(r);
        if ("body".equals(name)) body = r;
        else if ("head".equals(name)) head = r;
        else if ("earLeft".equals(name)) earLeft = r;
        else if ("earRight".equals(name)) earRight = r;
        else if ("tail".equals(name)) tail = r;
        else if ("legFrontLeft".equals(name)) legFrontLeft = r;
        else if ("legFrontRight".equals(name)) legFrontRight = r;
        else if ("legBackLeft".equals(name)) legBackLeft = r;
        else if ("legBackRight".equals(name)) legBackRight = r;
    }

    void box(String group, float px, float py, float pz, float rx, float ry, float rz, int u, int v, float x,
            float y, float z, int dx, int dy, int dz, float delta, boolean mirror) {
        ModelRenderer r = new ModelRenderer(model);
        r.setTextureSize(texW, texH);
        r.setRotationPoint(px, py, pz);
        r.rotateAngleX = rx;
        r.rotateAngleY = ry;
        r.rotateAngleZ = rz;
        r.mirror = mirror;
        r.cubeList.add(new ModelBox(r, u, v, x, y, z, dx, dy, dz, delta));
        groups.get(group).addChild(r);
    }

    /** Back to the standing pose of the pack. */
    void reset() {
        for (Map.Entry<String, ModelRenderer> e : groups.entrySet()) {
            float[] p = rest.get(e.getKey());
            ModelRenderer r = e.getValue();
            r.setRotationPoint(p[0], p[1], p[2]);
            r.rotateAngleX = r.rotateAngleY = r.rotateAngleZ = 0.0F;
        }
    }

    void render(float scale) {
        if (this.scale == 1.0F) {
            renderParts(scale);
            return;
        }
        GL11.glPushMatrix();
        float feet = 24.0F * scale; // keep the paws on the ground
        GL11.glTranslatef(0.0F, feet * (1.0F - this.scale), 0.0F);
        GL11.glScalef(this.scale, this.scale, this.scale);
        renderParts(scale);
        GL11.glPopMatrix();
    }

    private void renderParts(float scale) {
        body.render(scale);
        tail.render(scale);
        legFrontLeft.render(scale);
        legFrontRight.render(scale);
        legBackLeft.render(scale);
        legBackRight.render(scale);
        if (headScale == 1.0F) {
            head.render(scale);
        } else {
            GL11.glPushMatrix();
            GL11.glTranslatef(head.rotationPointX * scale, head.rotationPointY * scale, head.rotationPointZ * scale);
            GL11.glScalef(headScale, headScale, headScale);
            GL11.glTranslatef(-head.rotationPointX * scale, -head.rotationPointY * scale,
                    -head.rotationPointZ * scale);
            head.render(scale);
            GL11.glPopMatrix();
        }
    }
}
