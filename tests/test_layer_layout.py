"""Verify the metadata is split into self-consistent Yocto layers.

These are fast static checks - no BitBake or QEMU needed.  They guard the
split of the former single repository-root layer into the BSP, distro, and
application layers.
"""

import glob
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# Layer directory -> expected (collection, priority).
EXPECTED_LAYERS = {
    "meta-k230-bsp": ("k230", "6"),
    "meta-r2os-apps": ("r2os-apps", "6"),
    "meta-r2os-distro": ("r2os", "7"),
}

# Collection -> collections it declares in LAYERDEPENDS.
EXPECTED_DEPENDENCIES = {
    "k230": ["core"],
    "r2os-apps": ["core"],
    "r2os": ["core", "k230", "r2os-apps"],
}

# BBLAYERS order in the sample must satisfy the dependencies.
EXPECTED_BBLAYERS_ORDER = [
    "/work/src/meta-k230-bsp",
    "/work/src/meta-r2os-apps",
    "/work/src/meta-r2os-distro",
]

SERIES = "scarthgap wrynose"


def _read(path):
    return path.read_text()


def _active(text):
    """Drop comment lines so commented-out history cannot match."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )


def _layer_confs():
    return {
        name: _active(_read(REPO_ROOT / name / "conf" / "layer.conf"))
        for name in EXPECTED_LAYERS
    }


def _match(text, pattern, label):
    match = re.search(pattern, text, re.MULTILINE)
    assert match, f"{label}: pattern not found: {pattern}"
    return match


class LayerDeclarationTest(unittest.TestCase):
    def test_layer_directories_exist(self):
        for name in EXPECTED_LAYERS:
            conf = REPO_ROOT / name / "conf" / "layer.conf"
            self.assertTrue(conf.is_file(), f"missing layer file: {conf}")

    def test_repository_root_is_not_a_layer(self):
        self.assertFalse(
            (REPO_ROOT / "conf" / "layer.conf").exists(),
            "repository root must not declare a layer after the split",
        )

    def test_collections_and_priorities(self):
        for name, (collection, priority) in EXPECTED_LAYERS.items():
            text = _layer_confs()[name]
            actual = _match(
                text, r'^BBFILE_COLLECTIONS \+=\s*"([^"]+)"', name
            ).group(1)
            self.assertEqual(actual, collection, f"{name}: collection")
            actual = _match(
                text, r'^BBFILE_PRIORITY_\S+\s*=\s*"([^"]+)"', name
            ).group(1)
            self.assertEqual(actual, priority, f"{name}: priority")

    def test_layer_series_compatibility(self):
        for name, text in _layer_confs().items():
            actual = _match(
                text, r'^LAYERSERIES_COMPAT_\S+\s*=\s*"([^"]+)"', name
            ).group(1)
            self.assertEqual(actual, SERIES, f"{name}: LAYERSERIES_COMPAT")

    def test_layer_dependencies(self):
        for name, text in _layer_confs().items():
            actual = _match(
                text, r'^LAYERDEPENDS_\S+\s*=\s*"([^"]*)"', name
            ).group(1).split()
            collection = EXPECTED_LAYERS[name][0]
            self.assertEqual(
                actual, EXPECTED_DEPENDENCIES[collection],
                f"{name}: LAYERDEPENDS",
            )

    def test_layer_dependencies_resolve_and_are_acyclic(self):
        provided = {"core"} | {
            collection for collection, _priority in EXPECTED_LAYERS.values()
        }
        for collection, dependencies in EXPECTED_DEPENDENCIES.items():
            for dependency in dependencies:
                self.assertIn(
                    dependency, provided,
                    f"{collection}: dependency {dependency} not provided",
                )

        # Walk the graph from every collection; a node that can reach itself
        # means the dependency graph contains a cycle.
        def reachable(start):
            seen, stack = set(), [start]
            while stack:
                node = stack.pop()
                for dependency in EXPECTED_DEPENDENCIES.get(node, []):
                    if dependency not in seen:
                        seen.add(dependency)
                        stack.append(dependency)
            return seen

        for node in EXPECTED_DEPENDENCIES:
            self.assertNotIn(
                node, reachable(node), f"dependency cycle at {node}"
            )

    def test_layers_do_not_set_unpackdir(self):
        # Wrynose defines UNPACKDIR as ${WORKDIR}/sources and insane.bbclass
        # aborts every recipe whose UNPACKDIR resolves to WORKDIR.  A layer.conf
        # assignment also reaches oe-core recipes, so no layer may set it; the
        # scarthgap compatibility default lives in scripts/yocto-host-build.
        for name, text in _layer_confs().items():
            self.assertNotIn(
                "UNPACKDIR", text,
                f"{name}: layer.conf must not set UNPACKDIR",
            )

    def test_host_build_restores_legacy_unpackdir_for_scarthgap(self):
        text = _read(REPO_ROOT / "scripts" / "yocto-host-build")
        self.assertIn("append_legacy_unpackdir_conf", text)
        self.assertIn('UNPACKDIR = "${WORKDIR}"', text)

    def test_every_layer_provides_recipes(self):
        for name in EXPECTED_LAYERS:
            recipes = (
                glob.glob(str(REPO_ROOT / name / "recipes-*" / "*" / "*.bb"))
                + glob.glob(
                    str(REPO_ROOT / name / "recipes-*" / "*" / "*.bbappend")
                )
            )
            self.assertTrue(recipes, f"{name}: BBFILES matches no recipes")


class LayerOwnershipTest(unittest.TestCase):
    def test_no_recipe_directory_at_repository_root(self):
        stray = sorted(
            path.name
            for path in REPO_ROOT.glob("recipes-*")
            if path.is_dir()
        )
        self.assertEqual(stray, [], f"recipe directories left at root: {stray}")

    def test_recipes_live_in_exactly_one_layer(self):
        owners = {}
        for name in EXPECTED_LAYERS:
            for path in glob.glob(
                str(REPO_ROOT / name / "recipes-*" / "*" / "*")
            ):
                if Path(path).suffix not in (".bb", ".bbappend"):
                    continue
                relative = str(Path(path).relative_to(REPO_ROOT))
                owners.setdefault(relative, []).append(name)

        duplicated = {
            path: names for path, names in owners.items() if len(names) > 1
        }
        self.assertEqual(duplicated, {}, f"recipes owned twice: {duplicated}")

        on_disk = {
            str(path.relative_to(REPO_ROOT))
            for layer in EXPECTED_LAYERS
            for path in REPO_ROOT.glob(f"{layer}/recipes-*/*/*.bb*")
        }
        self.assertEqual(
            sorted(on_disk), sorted(owners),
            "every recipe must be claimed by a layer",
        )

    def test_fragment_files_follow_layer_ownership(self):
        # OE_FRAGMENTS entries such as "machine/k230-canmv" and "distro/r2os"
        # are built-in fragments: oe-core sets
        # OE_FRAGMENTS_BUILTIN = "machine:MACHINE distro:DISTRO", so BitBake
        # expands them to plain variable assignments instead of requiring a
        # fragment file.  These files therefore document the fragment and let
        # tooling list it; they follow the layer that owns the setting.
        self.assertTrue(
            (REPO_ROOT / "meta-k230-bsp/conf/fragments/machine/k230-canmv.conf").is_file(),
            "machine fragment belongs to the BSP layer",
        )
        self.assertTrue(
            (REPO_ROOT / "meta-r2os-distro/conf/fragments/distro/r2os.conf").is_file(),
            "distro fragment belongs to the distro layer",
        )

    def test_bsp_layer_owns_machine_kernel_and_wic(self):
        bsp = REPO_ROOT / "meta-k230-bsp"
        self.assertTrue((bsp / "conf/machine/k230-canmv.conf").is_file())
        self.assertTrue((bsp / "recipes-kernel/linux/linux-k230_6.18.bb").is_file())
        self.assertTrue((bsp / "recipes-bsp/opensbi/opensbi_%.bbappend").is_file())
        self.assertTrue((bsp / "wic/k230-canmv-sdimage.wks").is_file())

        text = _layer_confs()["meta-k230-bsp"]
        self.assertIn('WKS_SEARCH_PATH:append = ":${K230BASE}/wic"', text)

    def test_apps_layer_owns_application_recipes(self):
        apps = REPO_ROOT / "meta-r2os-apps" / "recipes-support"
        for recipe in ("fastfetch", "picoclaw"):
            matches = glob.glob(str(apps / recipe / "*.bb"))
            self.assertTrue(matches, f"meta-r2os-apps: missing {recipe}")

    def test_distro_layer_owns_policy_and_image(self):
        distro = REPO_ROOT / "meta-r2os-distro"
        self.assertTrue((distro / "conf/distro/r2os.conf").is_file())
        self.assertTrue((distro / "recipes-core/images/r2os-image.bb").is_file())
        self.assertTrue(
            (distro / "recipes-core/packagegroups/packagegroup-k230-common.bb").is_file()
        )
        self.assertTrue(
            (distro / "conf/templates/default/bblayers.conf.sample").is_file()
        )


class LayerWiringTest(unittest.TestCase):
    def test_bblayers_sample_lists_split_layers_in_order(self):
        sample = REPO_ROOT / "meta-r2os-distro/conf/templates/default/bblayers.conf.sample"
        text = _read(sample)
        positions = []
        for layer in EXPECTED_BBLAYERS_ORDER:
            self.assertIn(f"  {layer} \\", text, f"bblayers sample: {layer}")
            positions.append(text.index(f"  {layer} \\"))
        self.assertEqual(
            positions, sorted(positions), "bblayers sample: dependency order"
        )

    def test_container_setup_adds_every_layer(self):
        text = _read(REPO_ROOT / "scripts/yocto-k230-setup")
        for layer in EXPECTED_BBLAYERS_ORDER:
            self.assertIn(layer, text, f"yocto-k230-setup: {layer}")
        self.assertNotIn(
            "\n    /work/src\n", text,
            "yocto-k230-setup: repository root must not be added as a layer",
        )

    def test_host_setup_adds_every_layer(self):
        text = _read(REPO_ROOT / "scripts/yocto-host-build")
        for layer in EXPECTED_BBLAYERS_ORDER:
            name = layer.rsplit("/", 1)[-1]
            self.assertIn(
                f'"$repo_root/{name}"', text, f"yocto-host-build: {name}"
            )
        self.assertNotIn(
            '    "$repo_root" \\', text,
            "yocto-host-build: repository root must not be added as a layer",
        )


if __name__ == "__main__":
    unittest.main()
