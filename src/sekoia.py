import base64
import os
import time
from datetime import datetime, timedelta
from posixpath import join as urljoin
from typing import Any, Iterable, List, Set, Dict

import requests
import yaml
from pycti import OpenCTIConnectorHelper, get_config_variable
from requests import RequestException


class Sekoia(object):

    limit = 20

    def __init__(self):
        # Instantiate the connector helper from config
        config_file_path = os.path.dirname(os.path.abspath(__file__)) + "/config.yml"
        config = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )
        self.helper = OpenCTIConnectorHelper(config)
        self._cache = {}
        # Extra config
        self.base_url = self.get_config("base_url", config, "https://api.sekoia.io")
        self.collection = self.get_config(
            "collection", config, "d6092c37-d8d7-45c3-8aff-c4dc26030608"
        )
        self.api_key = self.get_config("api_key", config)
        if not self.api_key:
            self.helper.log_error("API key is Missing")
            raise ValueError("API key is Missing")

    def run(self):
        self.helper.log_info("Starting SEKOIA.IO connector")
        state = self.helper.get_state() or {}
        cursor = state.get("last_cursor", self.generate_first_cursor())
        while True:
            try:
                cursor = self._run(cursor)
                self.helper.set_state({"last_cursor": cursor})
            except (KeyboardInterrupt, SystemExit):
                self.helper.log_info("Connector stop")
                exit(0)
            except Exception as ex:
                self.helper.log_error(str(ex))
            time.sleep(60)

    @staticmethod
    def get_config(name: str, config, default: Any = None):
        env_name = f"SEKOIA_{name.upper()}"
        result = get_config_variable(env_name, ["sekoia", name], config)
        return result or default

    def get_collection_url(self):
        return urljoin(
            self.base_url, "v2/inthreat/collections", self.collection, "objects"
        )

    def get_object_url(self, ids: Iterable):
        return urljoin(self.base_url, "v2/inthreat/objects", ",".join(ids))

    def get_relationship_url(self, ids: Iterable):
        return urljoin(self.base_url, "v2/inthreat/relationships", ",".join(ids))

    @staticmethod
    def generate_first_cursor() -> str:
        """
        Generate the first cursor to interrogate the API
        so we don't start at the beginning.
        """
        start = f"{(datetime.utcnow() - timedelta(hours=1)).isoformat()}Z"
        return base64.b64encode(start.encode("utf-8")).decode("utf-8")

    @staticmethod
    def chunks(items, chunk_size):
        """
        Yield successive n-sized chunks from items.
        """
        for i in range(0, len(items), chunk_size):
            yield items[i : i + chunk_size]

    def _run(self, cursor):
        params = {"limit": self.limit, "cursor": cursor}

        data = self._send_request(self.get_collection_url(), params)
        if not data:
            return cursor

        next_cursor = data["next_cursor"] or cursor  # In case next_cursor is None
        items = data["items"]
        if not items:
            return next_cursor

        items = self._retrieve_references(items)
        bundle = self.helper.stix2_create_bundle(items)
        self.helper.send_stix2_bundle(bundle, update=True)

        if len(items) < self.limit:
            # We got the last results
            return next_cursor

        # More results to fetch
        return self._run(next_cursor)

    def _retrieve_references(
        self, items: List[Dict], current_depth: int = 0
    ) -> List[Dict]:
        """
        Retrieve the references that appears in the given items.

        To avoid having an infinite recursion a safe guard has been implemented.
        """
        if current_depth == 5:
            # Safe guard to avoid infinite recursion if an object was not found for example
            return items

        to_fetch = self._get_missing_refs(items)
        for ref in list(to_fetch):
            if ref in self._cache:
                items.append(self._cache[ref])
                to_fetch.remove(ref)
        if not to_fetch:
            return items

        objects_to_fetch = [i for i in to_fetch if not i.startswith("relationship--")]
        items += self._retrieve_by_ids(objects_to_fetch, self.get_object_url)

        relationships_to_fetch = [i for i in to_fetch if i.startswith("relationship--")]
        items += self._retrieve_by_ids(
            relationships_to_fetch, self.get_relationship_url
        )
        return self._retrieve_references(items, current_depth + 1)

    def _get_missing_refs(self, items: List[Dict]) -> Set:
        """
        Get the object's references that are missing
        """
        ids = {item["id"] for item in items}
        refs = set()
        for item in items:
            refs.update(item.get("object_marking_refs", []))
            if item.get("created_by_ref"):
                refs.add(item["created_by_ref"])
            if item["type"] == "report":
                refs.update(item.get("object_refs", []))
            if item["type"] == "relationship":
                refs.add(item["source_ref"])
                refs.add(item["target_ref"])
        return refs - ids

    def _retrieve_by_ids(self, ids, url_callback):
        """
        Fetch the items for the given ids.
        """
        items = []
        for chunk in self.chunks(ids, 40):
            url = url_callback(chunk)
            res = self._send_request(url)
            if not res:
                continue
            if "items" in res:
                items.extend(res["items"])
                for item in res["items"]:
                    self._add_to_cache_if_needed(item)
            if "data" in res:
                items.append(res["data"])
                self._add_to_cache_if_needed(res["data"])
        return items

    def _add_to_cache_if_needed(self, item):
        """
        Add item to the cache only if it is an identity or a marking definition
        """
        if item["id"].startswith("marking-definition--") or item["id"].startswith(
            "identity--"
        ):
            self._cache[item["id"]] = item

    def _send_request(self, url, params=None):
        """
        Sends the HTTP request and handle the errors
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            res = requests.get(url, params=params, headers=headers)
            res.raise_for_status()
            return res.json()
        except RequestException as ex:
            if ex.response:
                error = f"Request failed with status: {ex.response.status_code}"
                self.helper.log_error(error)
            else:
                self.helper.log_error(str(ex))
            return None


if __name__ == "__main__":
    try:
        sekoiaConnector = Sekoia()
        sekoiaConnector.run()
    except Exception:
        time.sleep(10)
        exit(0)
