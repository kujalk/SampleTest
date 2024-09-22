local json = require "json"
local base64 = require "base64"

-- Function to decode JWT token from Authorization header
local function decodeJwt(authorizationHeader)
  local headerFields = core.tokenize(authorizationHeader, " .")
  if #headerFields ~= 3 then
    core.log(6, "Improperly formatted Authorization header. 3 token sections required.")
    return nil
  end
  
  local token = {}
  token.payload = headerFields[2]
  token.payloaddecoded = json.decode(base64.decode(token.payload))
  
  return token
end

-- Main function to verify the token
function verify_token(txn)
  local auth_header = core.tokenize(txn.sf:hdr("authorization"), " ")
  if auth_header == nil then
    core.log(6, "No authorization token found")
    goto out
  end

  local token = decodeJwt(auth_header[2])
  if token == nil then
    core.log(6, "Token could not be decoded")
    goto out
  end

  -- Extract 'role' from the token and assign to 'clientid'
  local clientid = token.payloaddecoded.role
  core.log(6, "Role from token payload: " .. clientid)  -- Log the role

  -- Set the 'clientid' as a transaction variable
  txn.set_var(txn, "txn.clientid", clientid)

  core.log(6, "Token is valid, clientid: " .. clientid)
  txn.set_var(txn, "txn.authorized", true)
  do return end

  ::out::
  core.log(6, "Token not authorized")
  txn.set_var(txn, "txn.authorized", false)
  return nil
end

-- Register the token verification function
core.register_action("verify_token", {"http-req"}, verify_token)
