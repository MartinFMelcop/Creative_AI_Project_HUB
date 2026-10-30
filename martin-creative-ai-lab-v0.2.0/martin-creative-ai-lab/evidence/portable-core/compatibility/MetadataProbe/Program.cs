using System;
using System.IO;
using System.Linq;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Text.Json;
var rows = args.Select(path => {
 using var stream=File.OpenRead(path);using var pe=new PEReader(stream);var reader=pe.GetMetadataReader();string? target=null;
 foreach(var handle in reader.GetAssemblyDefinition().GetCustomAttributes()) {
  var attribute=reader.GetCustomAttribute(handle);if(attribute.Constructor.Kind!=HandleKind.MemberReference)continue;
  var constructor=reader.GetMemberReference((MemberReferenceHandle)attribute.Constructor);if(constructor.Parent.Kind!=HandleKind.TypeReference)continue;
  var type=reader.GetTypeReference((TypeReferenceHandle)constructor.Parent);
  if(reader.GetString(type.Namespace)=="System.Runtime.Versioning"&&reader.GetString(type.Name)=="TargetFrameworkAttribute") {
   var blob=reader.GetBlobReader(attribute.Value);if(blob.ReadUInt16()!=1)throw new InvalidDataException("Invalid attribute prolog");target=blob.ReadSerializedString();
  }
 }
 return new {path,target_framework=target,assembly_references=reader.AssemblyReferences.Select(h=>reader.GetString(reader.GetAssemblyReference(h).Name)).ToArray()};
}).ToArray();Console.WriteLine(JsonSerializer.Serialize(rows));
