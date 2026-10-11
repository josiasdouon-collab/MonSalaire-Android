"""Choisir une image (galerie) ou prendre une photo, sans permission speciale.

pick(callback, camera=False, workdir=".") -> callback(chemin_fichier | None, erreur | "")
Android : intentions systeme via pyjnius. Windows/Linux : boite de dialogue tkinter.
"""
import os
import time

from kivy.utils import platform

REQ = 7701


def pick(callback, camera=False, workdir="."):
    if platform == "android":
        _android(callback, camera, workdir)
    else:
        _desktop(callback)


def _desktop(callback):
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Choisir la photo du reçu",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp"), ("Tous", "*.*")])
        root.destroy()
        callback(path or None, "")
    except Exception as exc:
        callback(None, "Sélecteur de fichier indisponible : " + str(exc))


def _android(callback, camera, workdir):
    try:
        from android import activity
        from jnius import autoclass, cast, jarray
        Activity = autoclass("org.kivy.android.PythonActivity").mActivity
        Intent = autoclass("android.content.Intent")
        dest = os.path.join(workdir, f"recu_{int(time.time())}.jpg")
        state = {"uri": None}

        if camera:
            MediaStore = autoclass("android.provider.MediaStore")
            Values = autoclass("android.content.ContentValues")
            vals = Values()
            vals.put("mime_type", "image/jpeg")
            vals.put("_display_name", f"recu_{int(time.time())}.jpg")
            uri = Activity.getContentResolver().insert(
                MediaStore.Images.Media.EXTERNAL_CONTENT_URI, vals)
            state["uri"] = uri
            intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            intent.putExtra(MediaStore.EXTRA_OUTPUT, cast("android.os.Parcelable", uri))
            intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
                            Intent.FLAG_GRANT_READ_URI_PERMISSION)
        else:
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.setType("image/*")
            intent.addCategory(Intent.CATEGORY_OPENABLE)

        def on_result(request, result, data):
            if request != REQ:
                return
            activity.unbind(on_activity_result=on_result)
            try:
                if result != -1:  # RESULT_OK
                    callback(None, "")
                    return
                uri = state["uri"] if camera else data.getData()
                stream = Activity.getContentResolver().openInputStream(uri)
                out = autoclass("java.io.FileOutputStream")(dest)
                buf = jarray("b")(65536)
                while True:
                    n = stream.read(buf)
                    if n <= 0:
                        break
                    out.write(buf, 0, n)
                out.close()
                stream.close()
                callback(dest, "")
            except Exception as exc:
                callback(None, "Photo inaccessible : " + str(exc))

        activity.bind(on_activity_result=on_result)
        Activity.startActivityForResult(intent, REQ)
    except Exception as exc:
        callback(None, "Impossible d'ouvrir l'appareil photo / la galerie : " + str(exc))
