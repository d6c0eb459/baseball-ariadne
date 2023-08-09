import ariadne
import ariadne.wsgi

type_defs = ariadne.gql("""
    type Query {
        hello: String!
    }
""")

query = ariadne.QueryType()

@query.field("hello")
def resolve_hello(obj, info):
    return "Hi there"

schema = ariadne.make_executable_schema(type_defs, query)

app = ariadne.wsgi.GraphQL(schema, debug=True)
