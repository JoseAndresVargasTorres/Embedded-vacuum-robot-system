# Recompilar imagen y flashear microSD (/dev/sda)

Este flujo recompila la imagen completa y luego la flashea en la microSD detectada como:
- /dev/sda
- /dev/sda1 montada en /media/jose/boot
- /dev/sda2 montada en /media/jose/root

## 1) Recompilar imagen completa

```bash
cd ~/poky
source oe-init-build-env
bitbake robot-image
```

## 2) Verificar que la imagen se genero

```bash
ls -lh ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/robot-image-raspberrypi4-64.wic.bz2
ls -lh ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/robot-image-raspberrypi4-64.manifest
```

## 3) Flashear en la microSD /dev/sda

```bash
sudo umount /dev/sda1 2>/dev/null || true
sudo umount /dev/sda2 2>/dev/null || true
cd ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/
sudo bmaptool copy robot-image-raspberrypi4-64.wic.bz2 /dev/sda
sudo sync
```

## 4) Ajuste final en boot (quitar vc4-kms-v3d)

```bash
sudo mkdir -p /mnt/rpiboot
sudo mount /dev/sda1 /mnt/rpiboot
sudo sed -i 's/dtoverlay=vc4-kms-v3d//' /mnt/rpiboot/config.txt
sudo sync
sudo umount /mnt/rpiboot
```

## 5) Verificacion del ajuste (opcional pero recomendado)

```bash
sudo mount /dev/sda1 /mnt/rpiboot
grep -n '^dtoverlay=vc4-kms-v3d$' /mnt/rpiboot/config.txt || echo 'VC4_ELIMINADO_OK'
sudo umount /mnt/rpiboot
```

## 6) Expulsar microSD

```bash


sudo eject /dev/sda
echo "Listo"
```

## 7) Comando unico (todo seguido)

```bash
cd ~/poky && \
source oe-init-build-env && \
bitbake robot-image && \
sudo umount /dev/sda1 2>/dev/null || true; \
sudo umount /dev/sda2 2>/dev/null || true; \
cd ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/ && \
sudo bmaptool copy robot-image-raspberrypi4-64.wic.bz2 /dev/sda && \
sudo sync && \
sudo mkdir -p /mnt/rpiboot && \
sudo mount /dev/sda1 /mnt/rpiboot && \
sudo sed -i 's/dtoverlay=vc4-kms-v3d//' /mnt/rpiboot/config.txt && \
sudo sync && \
sudo umount /mnt/rpiboot && \
sudo eject /dev/sda && \
echo "Listo"
```

## 8) Seguridad minima antes de flashear

```bash
lsblk
```

Confirma otra vez que la microSD realmente es /dev/sda antes de ejecutar el paso 3.


sudo umount /dev/sda1 2>/dev/null
sudo umount /dev/sda2 2>/dev/null
cd ~/poky/build/tmp/deploy/images/raspberrypi4-64/
sudo bmaptool copy robot-image-raspberrypi4-64.wic.bz2 /dev/sda
sudo sync
sudo mkdir -p /mnt/rpiboot
sudo mount /dev/sda1 /mnt/rpiboot
sudo sed -i 's/dtoverlay=vc4-kms-v3d//' /mnt/rpiboot/config.txt
sudo sync
sudo umount /mnt/rpiboot
sudo eject /dev/sda
echo "✅ Listo"