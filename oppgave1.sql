-- Removed duplicates
DELETE FROM lego_inventory a
USING lego_inventory b
WHERE a.ctid < b.ctid
AND a.set_id = b.set_id
AND a.brick_type_id = b.brick_type_id
AND a.color_id = b.color_id;

-- Primary keys
ALTER TABLE lego_set ADD PRIMARY KEY (id);
ALTER TABLE lego_brick ADD PRIMARY KEY (brick_type_id, color_id);
ALTER TABLE lego_inventory ADD PRIMARY KEY (set_id, brick_type_id, color_id);

-- Foreign keys
ALTER TABLE lego_inventory
ADD FOREIGN KEY (set_id) REFERENCES lego_set(id);

ALTER TABLE lego_inventory
ADD FOREIGN KEY (brick_type_id, color_id)
REFERENCES lego_brick(brick_type_id, color_id);
