-- Function to parse a simple JSON-like string
local function simple_json_parse(json_str)
  local map = {}
  
  -- First, remove whitespace outside of quotes
  json_str = json_str:gsub("%s+", "")
  
  -- Remove outer braces
  json_str = json_str:match("^{(.+)}$")
  
  -- Process the content
  local pos = 1
  local len = #json_str
  
  while pos <= len do
    -- Find the next key
    local key_start, key_end = json_str:find('"[^"]*"', pos)
    if not key_start then break end
    
    local key = json_str:sub(key_start + 1, key_end - 1)
    pos = key_end + 1
    
    -- Skip colon
    if json_str:sub(pos, pos) == ":" then
      pos = pos + 1
    else
      break -- Malformed JSON
    end
    
    -- Check if value is an object
    if json_str:sub(pos, pos) == "{" then
      -- Find matching closing brace
      local brace_count = 1
      local value_start = pos
      pos = pos + 1
      
      while pos <= len and brace_count > 0 do
        if json_str:sub(pos, pos) == "{" then
          brace_count = brace_count + 1
        elseif json_str:sub(pos, pos) == "}" then
          brace_count = brace_count - 1
        end
        pos = pos + 1
      end
      
      local value_str = json_str:sub(value_start, pos - 1)
      map[key] = simple_json_parse(value_str) -- Recursively parse nested object
    else
      -- Value is a string
      local value_start, value_end = json_str:find('"[^"]*"', pos)
      if value_start then
        local value = json_str:sub(value_start + 1, value_end - 1)
        map[key] = value
        pos = value_end + 1
      else
        break -- Malformed JSON
      end
    end
    
    -- Skip comma if present
    if pos <= len and json_str:sub(pos, pos) == "," then
      pos = pos + 1
    end
  end
  
  return map
end

-- Function to read map file
local function read_map_file()
  local map = {}
  local file = io.open("/usr/local/etc/haproxy/mapfile.json", "r")
  
  if file then
    local content = file:read("*a")
    map = simple_json_parse(content) -- Use the simple JSON parser
    file:close()
    
    -- Log successful parsing
    core.log(6, "Successfully parsed map file")
  else
    core.log(6, "Error opening map file")
  end
  
  return map
end

-- Function to get specific limit
local function get_endpoint_limit(endpoint_id, method)
  local map = read_map_file()
  
  if map and map[endpoint_id] and map[endpoint_id][method] then
    return map[endpoint_id][method]
  else
    return nil
  end
end

-- Example usage
local function example()
  local get_limit = get_endpoint_limit("31090", "GET")
  if get_limit then
    core.log(6, "GET limit for endpoint 31090 is: " .. get_limit)
  else
    core.log(6, "Limit not found for endpoint 31090")
  end
end
