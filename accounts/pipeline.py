def populate_discord_fields(backend, user, response, *args, **kwargs):
    if backend.name != 'discord':
        return

    changed = False

    discord_id = str(response.get('id', ''))
    if discord_id and user.discord_id != discord_id:
        user.discord_id = discord_id
        changed = True

    # Discord provides 'global_name' (display name) and 'username' (the @handle).
    # global_name can be null on older accounts; fall back to username.
    display_name = response.get('global_name') or response.get('username', '')
    if display_name and user.display_name != display_name:
        user.display_name = display_name
        changed = True

    if changed:
        user.save()
