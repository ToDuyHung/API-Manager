import json

Byte = {
    'LF': '\\n',
    'NULL': '\\u0000'
}


class Frame:

    def __init__(self, command, headers, body):
        self.command = command
        self.headers = headers
        self.body = '' if body is None else body

    def __str__(self):
        lines = [self.command]
        skip_content_length = 'content-length' in self.headers
        if skip_content_length:
            del self.headers['content-length']

        for name in self.headers:
            value = self.headers[name]
            lines.append("" + name + ":" + value)

        if isinstance(self.body, dict):
            body_string = json.dumps(self.body, separators=(",", ":"))
            if self.body is not None and not skip_content_length:
                lines.append("content-length:" + str(len(body_string)))
            body_string = body_string.replace('"', '\\"')
        else:
            body_string = self.body
        lines.append(Byte['LF'] + body_string)
        return Byte["LF"].join(lines)

    @staticmethod
    def unmarshall_single(data):
        if len(data) <= 1:
            return Frame("", "", "")

        data = data[3:-2]
        lines = data.split(Byte['LF'])

        command = lines[0].strip()
        headers = {}

        # get all headers
        i = 1
        while lines[i] != '':
            # get key, value from raw header
            (key, value) = lines[i].split(':')
            headers[key] = value
            i += 1

        body = lines[i + 1]
        body = body.replace(Byte["NULL"], "").strip()
        if len(body) == 0:
            body = None
        return Frame(command, headers, body)

    @staticmethod
    def marshall(command, headers, body):
        return f'["{str(Frame(command, headers, body)) + Byte["NULL"]}"]'
